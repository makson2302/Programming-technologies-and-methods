"""Temperature measurement manager with GUI."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import List


class TemperatureMeasurement:
    """Represents a single temperature measurement."""

    def __init__(self, date_obj: date, location: str, value: float) -> None:
        """Initialize measurement.

        Args:
            date_obj: Date of measurement.
            location: Place where measured.
            value: Temperature value.
        """
        self.date = date_obj
        self.location = location
        self.value = value

    @staticmethod
    def from_string(line: str) -> 'TemperatureMeasurement':
        """Create measurement from a formatted string.

        Expected format:
            TemperatureMeasurement YYYY.MM.DD "location" value

        Args:
            line: Input string.

        Returns:
            TemperatureMeasurement object.
        """
        # Tokenization respecting quotes
        tokens = []
        current = []
        in_quotes = False

        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
                current.append(ch)
            elif ch.isspace() and not in_quotes:
                if current:
                    tokens.append(''.join(current))
                    current = []
            else:
                current.append(ch)
        if current:
            tokens.append(''.join(current))

        # Expected: type, date, location, value
        if len(tokens) != 4:
            raise ValueError(f"Invalid number of tokens: {tokens}")

        # First token must be "TemperatureMeasurement"
        if tokens[0] != "TemperatureMeasurement":
            raise ValueError(f"Unknown type: {tokens[0]}")

        date_str = tokens[1]
        year, month, day = map(int, date_str.split('.'))
        date_obj = date(year, month, day)

        location = tokens[2].strip('"')

        value = float(tokens[3])

        return TemperatureMeasurement(date_obj, location, value)

    def to_string(self) -> str:
        """Convert measurement to string for file storage.

        Returns:
            String in format: TemperatureMeasurement YYYY.MM.DD "location" value
        """
        date_str = self.date.strftime("%Y.%m.%d")
        # Ensure location is quoted
        return f'TemperatureMeasurement {date_str} "{self.location}" {self.value}'


class FileStorage:
    """Handles reading/writing measurements to a file."""

    def __init__(self, filename: str) -> None:
        """Initialize storage with file name.

        Args:
            filename: Path to data file.
        """
        self.filename = filename

    def load(self) -> List[TemperatureMeasurement]:
        """Read all measurements from file.

        Returns:
            List of TemperatureMeasurement objects.
        """
        measurements = []
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:  # skip empty lines
                        measurements.append(TemperatureMeasurement.from_string(line))
        except FileNotFoundError:
            # If file doesn't exist, return empty list
            pass
        return measurements

    def save(self, measurements: List[TemperatureMeasurement]) -> None:
        """Write measurements to file.

        Args:
            measurements: List of measurements to save.
        """
        with open(self.filename, 'w', encoding='utf-8') as file:
            for m in measurements:
                file.write(m.to_string() + '\n')


class Application:
    """Main GUI application."""

    def __init__(self, storage: FileStorage) -> None:
        """Initialize the window and widgets.

        Args:
            storage: FileStorage instance.
        """
        self.storage = storage
        self.measurements = storage.load()

        self.root = tk.Tk()
        self.root.title("Temperature Measurements")
        self.root.geometry("700x400")

        # Create table (Treeview)
        self.tree = ttk.Treeview(
            self.root,
            columns=("date", "location", "value"),
            show="headings"
        )
        self.tree.heading("date", text="Date")
        self.tree.heading("location", text="Location")
        self.tree.heading("value", text="Value (°C)")
        self.tree.column("date", width=100)
        self.tree.column("location", width=300)
        self.tree.column("value", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Input frame
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Date (YYYY.MM.DD):").grid(row=0, column=0, padx=5, pady=2)
        self.date_entry = ttk.Entry(input_frame, width=12)
        self.date_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Location:").grid(row=0, column=2, padx=5, pady=2)
        self.location_entry = ttk.Entry(input_frame, width=25)
        self.location_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(input_frame, text="Value:").grid(row=0, column=4, padx=5, pady=2)
        self.value_entry = ttk.Entry(input_frame, width=8)
        self.value_entry.grid(row=0, column=5, padx=5, pady=2)

        # Buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        add_btn = ttk.Button(btn_frame, text="Add", command=self.add_measurement)
        add_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_measurement)
        delete_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the Treeview with current measurements."""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert measurements
        for m in self.measurements:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    m.date.strftime("%Y.%m.%d"),
                    m.location,
                    f"{m.value:.2f}"
                )
            )

    def add_measurement(self) -> None:
        """Add a new measurement from entry fields."""
        date_str = self.date_entry.get().strip()
        location = self.location_entry.get().strip()
        value_str = self.value_entry.get().strip()

        if not date_str or not location or not value_str:
            messagebox.showerror("Error", "All fields must be filled")
            return

        try:
            # Parse date
            year, month, day = map(int, date_str.split('.'))
            date_obj = date(year, month, day)
            # Parse value
            value = float(value_str)

            # Create new measurement
            new_meas = TemperatureMeasurement(date_obj, location, value)
            self.measurements.append(new_meas)

            # Save to file
            self.storage.save(self.measurements)

            # Update UI
            self.refresh_table()
            self.clear_entries()

        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid data: {e}")

    def delete_measurement(self) -> None:
        """Delete selected measurement from the list."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No item selected")
            return

        # Get index of selected item
        index = self.tree.index(selected[0])
        if 0 <= index < len(self.measurements):
            del self.measurements[index]
            self.storage.save(self.measurements)
            self.refresh_table()

    def clear_entries(self) -> None:
        """Clear input fields."""
        self.date_entry.delete(0, tk.END)
        self.location_entry.delete(0, tk.END)
        self.value_entry.delete(0, tk.END)

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()


def main() -> None:
    """Entry point of the program."""
    storage = FileStorage("data.txt")
    app = Application(storage)
    app.run()


if __name__ == "__main__":
    main()
