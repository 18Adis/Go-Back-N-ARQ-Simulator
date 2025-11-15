import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageGrab
import time
import threading

class GoBackNSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Go-Back-N ARQ Simulator")
        # Adjusted geometry slightly to ensure capture
        self.root.geometry("1100x700+50+50") 
        self.root.configure(bg="#1e1e1e")

        # --- UI Elements ---
        control_frame = tk.Frame(root, bg="#1e1e1e")
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="Total Frames:", fg="white", bg="#1e1e1e").grid(row=0, column=0, padx=5)
        self.total_entry = tk.Entry(control_frame, width=5)
        self.total_entry.grid(row=0, column=1, padx=5)
        self.total_entry.insert(0, "15")

        tk.Label(control_frame, text="Window Size:", fg="white", bg="#1e1e1e").grid(row=0, column=2, padx=5)
        self.window_entry = tk.Entry(control_frame, width=5)
        self.window_entry.grid(row=0, column=3, padx=5)
        self.window_entry.insert(0, "4")

        tk.Label(control_frame, text="Lost Frames (comma-separated):", fg="white", bg="#1e1e1e").grid(row=0, column=4, padx=5)
        self.lost_entry = tk.Entry(control_frame, width=15)
        self.lost_entry.grid(row=0, column=5, padx=5)
        self.lost_entry.insert(0, "5, 9")

        self.start_button = tk.Button(control_frame, text="Start Simulation", bg="#007acc", fg="white", command=self.start_simulation)
        self.start_button.grid(row=0, column=6, padx=10)

        # "Save as GIF" button
        self.save_gif_button = tk.Button(control_frame, text="Save as GIF", bg="#2a9d8f", fg="white", command=self.save_gif, state=tk.DISABLED)
        self.save_gif_button.grid(row=0, column=7, padx=10)

        # --- Canvas for Visualization ---
        self.canvas = tk.Canvas(root, bg="#101010", width=1050, height=550)
        self.canvas.pack(pady=10)

        # --- Status Label ---
        self.status_label = tk.Label(root, text="Enter parameters and start simulation", fg="white", bg="#1e1e1e", font=("Consolas", 12))
        self.status_label.pack(pady=10)

        # Simulation state variables
        self.sender_frames = []
        self.receiver_frames = []
        self.sender_texts = []
        self.receiver_texts = []
        
        # List to store frames for GIF recording
        self.recorded_frames = []


    def capture_frame(self):
        """Captures the current state of the entire simulator window."""
        self.root.update_idletasks() # Ensure window dimensions are up-to-date
        
        # Get coordinates of the entire root window
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        x1 = x + self.root.winfo_width()
        y1 = y + self.root.winfo_height()
        
        # Grab the entire window
        self.recorded_frames.append(ImageGrab.grab(bbox=(x, y, x1, y1)))


    def draw_frame_lines(self):
        """Draws the static sender and receiver frame timelines."""
        self.canvas.delete("all")
        self.sender_frames.clear()
        self.receiver_frames.clear()
        self.sender_texts.clear()
        self.receiver_texts.clear()

        self.canvas.create_text(50, 50, text="SENDER", fill="cyan", font=("Consolas", 14, "bold"))
        self.canvas.create_text(50, 200, text="RECEIVER", fill="lime", font=("Consolas", 14, "bold"))

        box_width = 40
        spacing = 10
        start_x = 120
        y_sender = 50
        y_receiver = 200

        for i in range(self.total_frames):
            x = start_x + i * (box_width + spacing)
            # Sender boxes
            s_rect = self.canvas.create_rectangle(x, y_sender - 20, x + box_width, y_sender + 20, fill="#444", outline="white")
            s_text = self.canvas.create_text(x + box_width/2, y_sender, text=str(i), fill="white")
            self.sender_frames.append(s_rect)
            self.sender_texts.append(s_text)

            # Receiver boxes
            r_rect = self.canvas.create_rectangle(x, y_receiver - 20, x + box_width, y_receiver + 20, fill="#444", outline="white")
            r_text = self.canvas.create_text(x + box_width/2, y_receiver, text=str(i), fill="white")
            self.receiver_frames.append(r_rect)
            self.receiver_texts.append(r_text)

    def start_simulation(self):
        try:
            self.total_frames = int(self.total_entry.get())
            self.window_size = int(self.window_entry.get())
            lost_input = self.lost_entry.get().replace(" ", "")
            self.lost_frames = {int(x) for x in lost_input.split(",")} if lost_input else set()
            if self.total_frames > 20: # Limit frames to avoid clutter
                self.status_label.config(text="⚠️ Please use 20 or fewer total frames for best visibility.")
                return
        except ValueError:
            self.status_label.config(text="⚠️ Invalid input! Please check values.")
            return

        self.draw_frame_lines()
        
        # Prepare for recording
        self.recorded_frames.clear()
        self.start_button.config(state=tk.DISABLED)
        self.save_gif_button.config(state=tk.DISABLED)

        # Run simulation in a separate thread to keep UI responsive
        threading.Thread(target=self.run_protocol, daemon=True).start()

    def run_protocol(self):
        base = 0
        total_transmitted = 0

        # Create a window highlight rectangle
        window_rect = self.canvas.create_rectangle(0,0,0,0, outline="yellow", width=2)
        
        # Give UI time to draw initial state and capture it
        time.sleep(0.5) 
        self.capture_frame()

        while base < self.total_frames:
            # --- SENDING PHASE ---
            # Update window visualization
            start_x = 120 + base * 50 - 5
            end_x = 120 + min(base + self.window_size, self.total_frames) * 50 - 5
            self.canvas.coords(window_rect, start_x, 25, end_x, 75)
            self.status_label.config(text=f"Sending window: Frames {base} to {min(base + self.window_size, self.total_frames) - 1}")
            self.root.update()
            self.capture_frame()
            time.sleep(1)

            # Send all frames in the current window
            first_lost_in_window = -1
            for i in range(base, min(base + self.window_size, self.total_frames)):
                is_lost = i in self.lost_frames
                total_transmitted += 1

                self.canvas.itemconfig(self.sender_frames[i], fill="#007acc") # Blue for sent
                self.status_label.config(text=f"Transmitting Frame {i}...")
                
                success = self.animate_transmission(i, is_lost)

                if not success and first_lost_in_window == -1:
                    first_lost_in_window = i
                
                time.sleep(0.3)
                self.capture_frame()
            
            # --- RECEIVING & TIMEOUT PHASE ---
            if first_lost_in_window != -1:
                self.status_label.config(text=f"❌ Frame {first_lost_in_window} was lost. Simulating timeout.")
                self.capture_frame()
                time.sleep(1.5)
                self.status_label.config(text=f"TIMEOUT! Going back to Frame {first_lost_in_window}.")
                self.capture_frame()
                time.sleep(1.5)
                base = first_lost_in_window
                self.lost_frames.discard(first_lost_in_window)
            else:
                ack_to = min(base + self.window_size, self.total_frames)
                self.status_label.config(text=f"✅ Window received. Sending cumulative ACK for {ack_to}.")
                self.capture_frame()
                self.animate_ack(ack_to)
                time.sleep(1)
                base = ack_to # Slide window

        self.canvas.delete(window_rect)
        self.status_label.config(text=f"🎉 All frames sent successfully! Total transmissions: {total_transmitted}")
        self.capture_frame()
        self.start_button.config(state=tk.NORMAL)
        if self.recorded_frames:
             self.save_gif_button.config(state=tk.NORMAL)

    def animate_transmission(self, frame_num, is_lost):
        start_x = 120 + frame_num * 50 + 20
        y_start, y_end = 75, 175
        arrow = self.canvas.create_line(start_x, y_start, start_x, y_start + 10, arrow=tk.LAST, fill="white", width=2)
        
        for y in range(y_start, y_end, 5):
            self.canvas.coords(arrow, start_x, y_start, start_x, y + 10)
            self.root.update()
            self.capture_frame() # Capture each step of the animation
            time.sleep(0.01)
            
            if is_lost and y > (y_start + y_end) / 2:
                self.canvas.delete(arrow)
                loss_x = self.canvas.create_text(start_x, y + 10, text="X", fill="red", font=("Consolas", 20, "bold"))
                self.capture_frame()
                time.sleep(0.5)
                self.canvas.delete(loss_x)
                self.capture_frame()
                return False

        self.canvas.itemconfig(arrow, fill="lime")
        self.capture_frame()
        time.sleep(0.2)
        self.canvas.delete(arrow)

        is_expected = all(self.canvas.itemcget(self.receiver_frames[i], 'fill') != "#444" for i in range(frame_num))
        
        if is_expected:
            self.canvas.itemconfig(self.receiver_frames[frame_num], fill="green") # Green for received
        else:
            self.canvas.itemconfig(self.receiver_frames[frame_num], fill="orange") # Orange for discarded
            self.status_label.config(text=f"Frame {frame_num} received out of order. Discarded.")
            time.sleep(0.5)

        self.capture_frame()
        return True

    def animate_ack(self, ack_num):
        """Animates a cumulative ACK moving from receiver to sender."""
        self.status_label.config(text=f"Receiver sends ACK {ack_num}")
        x_start = 120 + (ack_num -1) * 50 + 20
        y_start, y_end = 175, 75
        ack_pkt = self.canvas.create_text(x_start, y_start, text=f"ACK{ack_num}", fill="lime", font=("Consolas", 10, "bold"))

        for y in range(y_start, y_end, -5):
            self.canvas.coords(ack_pkt, x_start, y)
            self.root.update()
            self.capture_frame() # Capture each step of animation
            time.sleep(0.01)
        
        time.sleep(0.5)
        self.canvas.delete(ack_pkt)
        self.capture_frame()

    def save_gif(self):
        """Saves the recorded frames as a GIF file."""
        if not self.recorded_frames:
            self.status_label.config(text="⚠️ No simulation has been run yet to save.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")],
            title="Save Simulation as GIF"
        )
        if not filepath: # User cancelled the dialog
            return

        try:
            self.status_label.config(text="⏳ Saving GIF... this may take a moment."); self.root.update()
            self.recorded_frames[0].save(
                filepath,
                save_all=True,
                append_images=self.recorded_frames[1:],
                optimize=False,
                duration=50,    # Time between frames in milliseconds
                loop=0          # Loop forever
            )
            self.status_label.config(text=f"✅ GIF saved successfully!")
        except Exception as e:
            self.status_label.config(text=f"❌ Error saving GIF: {e}")


if __name__ == "__main__":
    try:
        from PIL import Image, ImageGrab
    except ImportError:
        print("--------------------------------------------------")
        print("ERROR: Pillow library not found.")
        print("Please install it to run this simulator.")
        print("Run this command in your terminal:")
        print("pip install Pillow")
        print("--------------------------------------------------")
        exit()
        
    root = tk.Tk()
    app = GoBackNSimulator(root)
    root.mainloop()
