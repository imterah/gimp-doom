#!/usr/bin/env python3

from typing import Optional, Tuple

import threading
import socket
import shutil
import sys
import os

# getcwd() isn't really accurate. So we have to do this weird stuff
cwd = sys.argv[0]
cwd = cwd[:cwd.rindex("/")]

package_dirname   = os.path.join(cwd, "packages")
package64_dirname = os.path.join(cwd, "packages64")

is_running_doom = False

print(f"INIT: CWD is set to {cwd}")

if os.path.isdir(package_dirname):
    print("Package repository exists. Adding")
    sys.path.insert(0, package_dirname)

if os.path.isdir(package64_dirname):
    print("Package repository (for 64bit libraries) exists. Adding")
    sys.path.insert(0, package64_dirname)

import cydoomgeneric as cdg
import numpy as np

print(cdg)

import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp
gi.require_version("GimpUi", "3.0")
from gi.repository import GimpUi
gi.require_version("Gegl", "0.4")
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
gi.require_version("Babl", "0.1")
from gi.repository import Babl

import os
import sys

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

def read_bytes(conn: socket.socket, bytes_to_read: int) -> bytes:
    byte_data = bytes()

    while len(byte_data) < bytes_to_read:
        byte_data += conn.recv(bytes_to_read - len(byte_data))
    
    return byte_data

class DOOM(Gimp.PlugIn):
    def do_query_procedures(self):
        return [
            "plug-in-doom-game"
        ]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name,
                                            Gimp.PDBProcType.PLUGIN,
                                            self.run, None)

        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)

        procedure.set_menu_label(_("DOOM for GIMP"))
        procedure.set_icon_name(GimpUi.ICON_GEGL)
        procedure.add_menu_path("<Image>/Games")

        procedure.set_documentation(_("Port of the DOOM engine to GIMP 3.0 Alpha"),
                                    _("Port of the DOOM engine to GIMP 3.0 Alpha"),
                                    name)
        
        procedure.set_attribution("Greyson", "Greyson", "2024")

        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, config, run_data):
        if is_running_doom:
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        
        if n_drawables != 1:
            msg = _("Procedure '{}' only works with one drawable.").format(procedure.get_name())
            error = GLib.Error.new_literal(Gimp.PlugIn.error_quark(), msg, 0)
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, error)
        else:
            drawable = drawables[0]

        wad_file = ""

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
            gi.require_version("Gdk", "3.0")
            from gi.repository import Gdk

            GimpUi.init("gimp-doom.py")

            dialog = GimpUi.Dialog(use_header_bar=True,
                                   title=_("Specify WAD File"),
                                   role="gimp-doom-wad-file")

            dialog.add_button(_("_Cancel"), Gtk.ResponseType.CANCEL)
            dialog.add_button(_("_OK"), Gtk.ResponseType.OK)

            geometry = Gdk.Geometry()
            geometry.max_aspect = 0.2
            dialog.set_geometry_hints(None, geometry, Gdk.WindowHints.ASPECT)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            dialog.get_content_area().add(box)

            text_entry = Gtk.Entry()
            text_entry.set_text("")
            box.pack_start(text_entry, True, True, 0)

            box.show()

            while True:
                response = dialog.run()
                
                if response == Gtk.ResponseType.OK:
                    wad_file = text_entry.get_text()
                    dialog.destroy()
                    break
                else:
                    dialog.destroy()
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        intersect, x, y, width, height = drawable.mask_intersect()

        if wad_file == "":
            wad_file = os.path.join(cwd, "doom.wad")

        if intersect:
            Gegl.init(None)
            print(f"INFO: using wad file '{wad_file}'")

            procedure = Gimp.get_pdb().lookup_procedure("gimp-drawable-set-pixel")
            
            try:
                shutil.copy(wad_file, os.path.join(os.getcwd(), "DOOM.WAD"))
            except:
                print("Could not copy DOOM WAD file!")

                # TODO return types
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            
            main_rect = Gegl.Rectangle.new(x, y, width, height)
            shadow_buffer = drawable.get_shadow_buffer()

            def draw_frame(pixels: np.ndarray) -> None:
                pixel_data = bytes(pixels[:,:,[2,1,0]].reshape(-1))

                shadow_buffer.set(main_rect, "RGB u8", pixel_data)
                shadow_buffer.flush()

                drawable.merge_shadow(True)
                drawable.update(x, y, width, height)
                Gimp.displays_flush()

            session_id = len(list(filter(lambda s: s.startswith("doom-inputrelay-"), os.listdir("/tmp/")))) + 1
            unix_socket_path = f"/tmp/doom-inputrelay-{session_id}"

            current_inputs: list[Tuple[int, int]] = []

            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(unix_socket_path)

            print("** Input Relay is active **")
            print(f"with session ID: {session_id}")
            print(f"with socket path: '{unix_socket_path}'")
            print("** Input Relay is active **")

            def process_ir_connections():
                server.listen(1)
                conn, addr = server.accept()

                while True:
                    key_status = int(read_bytes(conn, 1)[0])
                    key = int(read_bytes(conn, 1)[0])
                    
                    current_inputs.append((key_status, key))

            ir_thread = threading.Thread(target=process_ir_connections)
            ir_thread.start()
            
            def get_key() -> Optional[Tuple[int, int]]:
                if len(current_inputs) != 0:
                    key_event = current_inputs.pop(0)
                    return key_event
            
            print("Starting DOOM...")
            cdg.init(int(width), int(height), draw_frame, get_key)
            cdg.main()
            
            Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

Gimp.main(DOOM.__gtype__, sys.argv)
