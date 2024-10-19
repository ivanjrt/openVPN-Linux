import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import time
import tempfile

class OpenVPNControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenVPN Control")
        self.root.geometry("520x675")  # Made window taller
        
        # VPN status
        self.vpn_running = False
        self.vpn_process = None
        self.config_file = None
        self.auth_file = None
        
        # Create main container with padding
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title Label
        title_label = ttk.Label(main_frame, text="OpenVPN Connection Manager", font=('Helvetica', 12, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Config file selection - now in its own LabelFrame
        self.config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        self.config_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        self.config_label = ttk.Label(self.config_frame, text="Config file:")
        self.config_label.grid(row=0, column=0, padx=5)
        
        self.config_path = ttk.Entry(self.config_frame, width=35)
        self.config_path.grid(row=0, column=1, padx=5)
        
        self.browse_button = ttk.Button(self.config_frame, text="Browse", command=self.browse_config)
        self.browse_button.grid(row=0, column=2, padx=5)
        
        # Credentials frame
        self.cred_frame = ttk.LabelFrame(main_frame, text="Credentials", padding="10")
        self.cred_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Username field
        self.username_label = ttk.Label(self.cred_frame, text="Username:")
        self.username_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.username_entry = ttk.Entry(self.cred_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Password field
        self.password_label = ttk.Label(self.cred_frame, text="Password:")
        self.password_label.grid(row=1, column=0, padx=5, pady=5)
        
        self.password_entry = ttk.Entry(self.cred_frame, width=30, show="●")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Control Frame for button and status
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, pady=20)
        
        # Create VPN control button - made larger and more prominent
        self.vpn_button = ttk.Button(control_frame, text="Connect VPN", command=self.toggle_vpn, width=20)
        self.vpn_button.grid(row=0, column=0, pady=5)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Status: Disconnected", font=('Helvetica', 10))
        self.status_label.grid(row=1, column=0, pady=5)
        
        # Output Frame
        output_frame = ttk.LabelFrame(main_frame, text="Connection Log", padding="10")
        output_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Create and configure output text area
        self.output_text = tk.Text(output_frame, height=12, width=50, wrap=tk.WORD)
        self.output_text.grid(row=0, column=0, pady=5)
        self.output_text.config(state=tk.DISABLED)
        
        # Add scrollbar to output text
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        # Bind window closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ... [Rest of the methods remain exactly the same as in the previous version] ...

    def create_auth_file(self):
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(f"{self.username_entry.get()}\n")
                temp_file.write(f"{self.password_entry.get()}\n")
                return temp_file.name
        except Exception as e:
            self.update_output(f"Error creating auth file: {str(e)}\n")
            return None

    def cleanup_auth_file(self):
        if self.auth_file and os.path.exists(self.auth_file):
            try:
                os.unlink(self.auth_file)
                self.auth_file = None
            except Exception as e:
                self.update_output(f"Error removing auth file: {str(e)}\n")

    def browse_config(self):
        filename = filedialog.askopenfilename(
            title="Select OpenVPN config file",
            filetypes=(("OpenVPN files", "*.ovpn"), ("All files", "*.*"))
        )
        if filename:
            self.config_path.delete(0, tk.END)
            self.config_path.insert(0, filename)
            self.config_file = filename
            
    def toggle_vpn(self):
        if not self.vpn_running:
            self.start_vpn()
        else:
            self.stop_vpn()
            
    def start_vpn(self):
        if not self.config_path.get():
            messagebox.showerror("Error", "Please select a config file first")
            return
            
        if not self.username_entry.get() or not self.password_entry.get():
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        self.auth_file = self.create_auth_file()
        if not self.auth_file:
            messagebox.showerror("Error", "Failed to create authentication file")
            return
            
        self.vpn_running = True
        self.vpn_button.config(text="Disconnect VPN")
        self.status_label.config(text="Status: Connecting...")
        
        self.username_entry.config(state="disabled")
        self.password_entry.config(state="disabled")
        
        self.vpn_thread = threading.Thread(target=self.run_vpn)
        self.vpn_thread.daemon = True
        self.vpn_thread.start()
        
    def stop_vpn(self):
        self.vpn_running = False
        if self.vpn_process:
            try:
                subprocess.run(['sudo', 'killall', 'openvpn'], check=True)
            except subprocess.CalledProcessError:
                pass
        
        self.username_entry.config(state="normal")
        self.password_entry.config(state="normal")
        
        self.cleanup_auth_file()
        self.vpn_button.config(text="Connect VPN")
        self.status_label.config(text="Status: Disconnected")
        self.update_output("VPN connection terminated.\n")
        
    def run_vpn(self):
        config_path = self.config_path.get()
        
        try:
            self.vpn_process = subprocess.Popen(
                ['pkexec', 'openvpn', '--config', config_path, '--auth-user-pass', self.auth_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.update_output(f"Starting OpenVPN with config: {config_path}\n")
            self.status_label.config(text="Status: Connected")
            
            while self.vpn_running:
                output = self.vpn_process.stdout.readline()
                if output:
                    self.update_output(output)
                if self.vpn_process.poll() is not None:
                    break
                    
        except Exception as e:
            self.update_output(f"Error: {str(e)}\n")
            self.status_label.config(text="Status: Error")
            self.stop_vpn()
            
    def update_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.vpn_running:
            self.stop_vpn()
        self.cleanup_auth_file()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OpenVPNControlGUI(root)
    root.mainloop()
