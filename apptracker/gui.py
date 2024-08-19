import tkinter as tk
from tkinter import font
from tkinter import ttk
import threading
import webbrowser
import pyperclip
from apptracker.backend import Backend 

# GUI Structure idealogy adopted from: https://stackoverflow.com/a/17470842
# Button callback and threading stuff from: https://stackoverflow.com/a/64038231 tysm!
class GUI(tk.Frame):
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        self.loading_event = threading.Event()

        self.backend = Backend()
        self.root = root

        self.job_count_label = ttk.Label(self, text="Loading....")
        self.job_count_label.grid(row=0, column=1, sticky='ns')

        self.jobs_to_apply_to = ttk.Label(self, text="")
        self.jobs_to_apply_to.grid(row=1, column=1, sticky='ns')

        self.columns = ("Company", "Role", "Source", "Location")
        self.job_gridlist = ttk.Treeview(self, columns=self.columns, height=30, selectmode='browse')

        for col in self.columns:
            self.job_gridlist.column(col, anchor='w', stretch=False)

            if col == 'Location':
                self.job_gridlist.heading(col, text=col, command=lambda: self.treeview_sort_column(self.job_gridlist, col, False), anchor='w')
            else:
                self.job_gridlist.heading(col, text=col, command=lambda: self.treeview_sort_column(self.job_gridlist, col, False), anchor='center')
        
        self.job_gridlist['show'] = 'headings' # Gets rid of the empty icon column.
        self.job_gridlist.grid(row=2, column=0, columnspan=3, sticky='news')

        # Scrollbar handling
        self.job_gridlist_horizontal_sb = ttk.Scrollbar(master=self, orient=tk.HORIZONTAL, command=self.job_gridlist.xview)
        self.job_gridlist_horizontal_sb.grid(row=3, column=0, columnspan=3, sticky='nwe')
        self.job_gridlist_vertical_sb = ttk.Scrollbar(master=self, orient=tk.VERTICAL, command=self.job_gridlist.yview)
        self.job_gridlist_vertical_sb.grid(row=2, column=0, columnspan=3, sticky='nse')
        self.job_gridlist.configure(xscroll=self.job_gridlist_horizontal_sb.set, yscroll=self.job_gridlist_vertical_sb.set)      
        self.job_gridlist.bind("<Double-1>", self.treeview_double_click)
        self.job_gridlist.bind("<Button-3>", self.treeview_copy_url)

        self.add_button = tk.Button(self, text = "Add", width=10, command = self.start_add_application)
        self.add_button.grid(row=4, column=0, padx=(5, 0), pady=(5, 5), sticky='w')

        self.refresh_button = tk.Button(self, text="⟳", command = self.load_data_into_window)
        self.refresh_button.grid(row=4, column=1)

        self.discard_button = tk.Button(self, text = "Discard", width=10, command = self.start_add_discard)
        self.discard_button.grid(row=4, column=2, padx=(0, 5), pady=(5, 5),  sticky='e')

        #self.job_gridlist.insert('', 'end', 'unique id', text="", values=('Toto', 'toto', 'Widget Tour'))
        # Resize window dynamically.
        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=1)
        self.grid_columnconfigure(2,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.grid_rowconfigure(1,weight=1)
        self.grid_rowconfigure(2,weight=1)
        self.grid_rowconfigure(3,weight=1)
        self.grid_rowconfigure(4,weight=1)
    
        self.load_data_into_window()

    # From: https://stackoverflow.com/a/46994404
    def treeview_sort_column(self, tv, col, reverse):
        l = [(self.job_gridlist.set(k, col), k) for k in self.job_gridlist.get_children('')]
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.job_gridlist.move(k, '', index)

        # reverse sort next time
        self.job_gridlist.heading(col, command=lambda: \
            self.treeview_sort_column(tv, col, not reverse))

    def treeview_double_click(self, _):
        item = self.job_gridlist.selection()
        if len(item) == 0:
            return
        webbrowser.open(self.job_gridlist.item(item[0], "text"), new=0, autoraise=True)

    def treeview_copy_url(self, _):
        item = self.job_gridlist.selection()
        if len(item) == 0:
            return
        
        pyperclip.copy(self.job_gridlist.item(item[0], "text"))

    def disable_buttons(self):
        """Shortcut to disable all buttons in the GUI."""
        self.add_button["state"] = "disabled"
        self.refresh_button["state"] = "disabled"
        self.discard_button["state"] = "disabled"

        self.update()

    def enable_buttons(self):
        """Shortcut to enable all buttons in the GUI."""
        self.add_button["state"] = "normal"
        self.refresh_button["state"] = "normal"
        self.discard_button["state"] = "normal"

        self.update()

    def set_labels(self):
        self.job_count_label['text'] = f"Jobs Applied To: {self.backend.jobs_applied_to_count}"
        self.jobs_to_apply_to['text'] = f"Jobs To Review: {str(len(self.backend.to_display_job_lsting))}"

    def generic_event_checker(self, event : threading.Event, callback):
        if not event.is_set():
            self.after(100, self.generic_event_checker, event, callback)
            return
        
        callback()
    
    def load_data_into_window_callback(self):
        #print("Call back received")

        # Delete everything from gridlist.
        for row in self.job_gridlist.get_children():
            self.job_gridlist.delete(row)
        
        # Add new listings.
        default_font = font.nametofont("TkHeadingFont")
        longest_text = [15, 15, 15, 15]
        for listing in self.backend.to_display_job_lsting:
            self.job_gridlist.insert('', 'end', None, text=listing.url, values=(
                    listing.company_name,
                    listing.job_title,
                    listing.source,
                    listing.location
                )
            )
            longest_text[0] = max(longest_text[0], default_font.measure(listing.company_name + "____"))
            longest_text[1] = max(longest_text[1], default_font.measure(listing.job_title + "____"))
            longest_text[2] = max(longest_text[2], default_font.measure(listing.source + "____"))
            longest_text[3] = max(longest_text[3], default_font.measure(listing.location + "____"))

        # Resize our gridlist columns nicely.
        for i, col in enumerate(self.columns):
            self.job_gridlist.column(col, width=longest_text[i])

        # Add label stuff
        self.set_labels()

        self.loading_event.clear()
        self.enable_buttons()
        #print("Call back done")

    def load_data_into_window(self):
        self.disable_buttons()

        # Hopefully maintaining one loading event prevents a mess of multiple loading calls.
        if self.loading_event.is_set():
            return

        self.loading_event = threading.Event()
        self.generic_event_checker(self.loading_event, self.load_data_into_window_callback)
        thread = threading.Thread(target=self.backend.load, args=(self.loading_event, ))
        thread.start()
    
    def add_application(self):
        self.set_labels()

        self.loading_event.clear()
        self.enable_buttons()

    def start_add_application(self):
        item = self.job_gridlist.selection()
        if len(item) == 0:
            return
        
        if self.loading_event.is_set():
            return

        self.disable_buttons()

        self.loading_event = threading.Event()
        self.generic_event_checker(self.loading_event, self.add_application)

        item_details = self.job_gridlist.item(item[0])
        self.job_gridlist.delete(item[0])

        thread = threading.Thread(target=self.backend.add_application, args=(self.loading_event,"Applied", item_details['values'][0], item_details['values'][1], item_details['values'][3], item_details['text']))
        thread.start()

    def start_add_discard(self):
        item = self.job_gridlist.selection()
        if len(item) == 0:
            return
        
        if self.loading_event.is_set():
            return

        self.disable_buttons()

        self.loading_event = threading.Event()
        self.generic_event_checker(self.loading_event, self.add_application)

        item_details = self.job_gridlist.item(item[0])
        self.job_gridlist.delete(item[0])

        thread = threading.Thread(target=self.backend.add_application, args=(self.loading_event, "Discarded", item_details['values'][0], item_details['values'][1], item_details['values'][3], item_details['text']))
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Job Application Tracker")
    # root.minsize(1200, 200)
    # root.resizable(False, False) 
    root.state('zoomed')

    GUI(root).pack(side="top", fill="both", expand=True)
    root.mainloop()