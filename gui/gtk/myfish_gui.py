#!/usr/bin/env python3
import gi, subprocess
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class MyFishApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="CommanderOS • MyFish")
        self.set_border_width(20)
        self.set_default_size(420, 300)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(box)

        title = Gtk.Label()
        title.set_markup("<span size='20000' weight='bold'>CommanderOS</span>")
        box.pack_start(title, False, False, 10)

        actions = [
            ("Restore Configs", "restore.sh"),
            ("Decrypt Secrets", "decrypt_secrets.sh"),
            ("Rebuild System", "rebuild.sh"),
            ("Run Autosync", "autosync.sh"),
        ]

        for label, script in actions:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.run_script, script)
            box.pack_start(btn, False, False, 0)

        quit_btn = Gtk.Button(label="Quit")
        quit_btn.connect("clicked", Gtk.main_quit)
        box.pack_end(quit_btn, False, False, 0)

    def run_script(self, widget, script):
        subprocess.Popen([
            "gnome-terminal", "--",
            "bash", "-c", f"~/MyFish/scripts/{script}; exec bash"
        ])

win = MyFishApp()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

