#!/usr/bin/env python3

import gi
import os
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

HOME = os.path.expanduser("~")
FLAG = f"{HOME}/.config/myfish_firstboot_done"
MYFISH = f"{HOME}/MyFish"

class CommanderRestore(Gtk.Window):
    def __init__(self):
        super().__init__(title="CommanderOS Setup")
        self.set_border_width(20)
        self.set_default_size(520, 280)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(vbox)

        logo = Gtk.Label()
        logo.set_markup(
            "<span font_desc='monospace 14' foreground='#4dd0e1'>"
            "██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ ███████╗\n"
            "██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝\n"
            "██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║█████╗  \n"
            "██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║██╔══╝  \n"
            "╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝███████╗\n"
            " ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝</span>"
        )
        vbox.pack_start(logo, False, False, 0)

        label = Gtk.Label(label="Restore your MyFish / CommanderOS setup?")
        vbox.pack_start(label, False, False, 0)

        btn_restore = Gtk.Button(label="Restore Everything")
        btn_restore.connect("clicked", self.restore)

        btn_skip = Gtk.Button(label="Skip")
        btn_skip.connect("clicked", self.skip)

        vbox.pack_start(btn_restore, True, True, 0)
        vbox.pack_start(btn_skip, True, True, 0)

    def restore(self, widget):
        subprocess.Popen(["bash", f"{MYFISH}/scripts/restore.sh"])
        self.finish()

    def skip(self, widget):
        self.finish()

    def finish(self):
        os.makedirs(os.path.dirname(FLAG), exist_ok=True)
        open(FLAG, "w").close()
        Gtk.main_quit()


win = CommanderRestore()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
