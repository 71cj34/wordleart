import tkinter as tk
from tkinter import messagebox
import requests
from datetime import datetime

def get_wordle_solution():
    current_date = datetime.now().strftime('%Y-%m-%d')
    url = f"https://www.nytimes.com/svc/wordle/v2/{current_date}.json"

    try:
        response = requests.get(url)

        response.raise_for_status()

        data = response.json()
        solution = data.get("solution")

        return solution

    except requests.exceptions.RequestException as e:
        return f"Error fetching Wordle: {e}"


class WordlePatternGUI:
    def __init__(self, root, dictionary_path="guesses.txt"):
        self.root = root
        self.root.title("Wordle Pattern Finder")
        self.dictionary_path = dictionary_path

        self.grid_vars = [[tk.IntVar() for _ in range(5)] for _ in range(6)]
        self.no_yellows_var = tk.BooleanVar(value=False)

        self.setup_ui()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack()

        tk.Label(main_frame, text="Set Green (1) tiles pattern:", font=('Arial', 12, 'bold')).pack(pady=5)

        tk.Checkbutton(main_frame, text="Strict Mode: Exclude Yellow Tiles",
                       variable=self.no_yellows_var, font=('Arial', 10, 'italic')).pack(pady=5)

        grid_frame = tk.Frame(main_frame)
        grid_frame.pack()

        for r in range(6):
            row_frame = tk.Frame(grid_frame)
            row_frame.pack()
            for c in range(5):
                cb = tk.Checkbutton(row_frame, variable=self.grid_vars[r][c],
                                   width=4, height=2, indicatoron=False,
                                   selectcolor="#6aaa64", background="#787c7e")
                cb.pack(side=tk.LEFT, padx=2, pady=2)

        self.search_btn = tk.Button(main_frame, text="Find Words", command=self.run_search,
                                   bg="#1a73e8", fg="white", font=('Arial', 10, 'bold'))
        self.search_btn.pack(pady=20)

    def get_masks(self):
        masks = []
        for r in range(6):
            row_val = 0
            for c in range(5):
                if self.grid_vars[r][c].get() == 1:
                    row_val |= (1 << (4 - c))
            masks.append(row_val)
        return masks

    def has_yellows(self, guess, secret, green_mask):

        secret_list = list(secret)
        for i in range(5):
            if (green_mask & (1 << (4 - i))):
                secret_list[i] = None # mask out green matches

        for i in range(5):
            if not (green_mask & (1 << (4 - i))):
                if guess[i] in secret_list:
                    return True
        return False

    def get_green_mask(self, guess, secret):
        mask = 0
        for i in range(5):
            if guess[i] == secret[i]:
                mask |= (1 << (4 - i))
        return mask

    def find_wordle_pattern(self, dictionary, target_masks, exclude_yellows):
        secret = get_wordle_solution()
        buckets = [[] for _ in range(6)]

        for word in dictionary:
            mask = self.get_green_mask(word, secret)
            for i in range(6):
                if mask == target_masks[i]:
                    # If "No Yellows" is on, verify there are zero partial matches
                    if exclude_yellows:
                        if not self.has_yellows(word, secret, mask):
                            buckets[i].append(word)
                    else:
                        buckets[i].append(word)

        if any(not b for b in buckets):
            return None, None

        solution = []
        def solve(row):
            if row == 6:
                return True
            for word in buckets[row]:
                if word in solution: continue
                solution.append(word)
                if solve(row + 1): return True
                solution.pop()
            return False

        if solve(0):
            return secret, solution
        return None, None

    def run_search(self):
        target_masks = self.get_masks()
        exclude_yellows = self.no_yellows_var.get()

        try:
            with open(self.dictionary_path, "r") as f:
                word_list = [line.strip().lower() for line in f.readlines() if len(line.strip()) == 5]
        except FileNotFoundError:
            messagebox.showerror("Error", f"Could not find {self.dictionary_path}")
            return

        secret, sol = self.find_wordle_pattern(word_list, target_masks, exclude_yellows)

        if secret:
            result_str = f"Secret: {secret}\n\nSteps:\n" + "\n".join(sol)
            messagebox.showinfo("Solution Found", result_str)
        else:
            messagebox.showwarning("No luck", "No combination found. Try unchecking 'Exclude Yellow Tiles'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordlePatternGUI(root)
    root.mainloop()
