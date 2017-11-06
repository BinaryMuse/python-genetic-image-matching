from os import system
from platform import system as platform

import tkinter as Tk
from PIL import Image, ImageDraw, ImageTk, ImageChops

from dna import Dna


class Candidate:
    def __init__(self, dna):
        self.dna = dna
        self._cached_image = None

    @classmethod
    def random(cls):
        """
        Generate a Candidate with 50 totally random Triangles.
        """
        dna = Dna.random()
        return cls(dna)

    def to_image(self):
        """
        Generate (and cache) a Pillow image made of this Candidate's Triangles.
        """
        if self._cached_image:
            return self._cached_image
        else:
            parsed = self.dna.parse()

            img = Image.new('RGB', (256, 256))
            drw = ImageDraw.Draw(img, 'RGBA')

            (bg_r, bg_g, bg_b) = parsed["bg"]
            drw.polygon([(0, 0), (0, 256), (256, 256), (256, 0)], (bg_r, bg_g, bg_b, 255))

            shapes = sorted(parsed["shapes"], key=lambda sh: sh["draw_order"])
            for s in shapes:
                drw.polygon(s["verticies"], s["color"])

            del drw
            self._cached_image = img
            return img

    def copy(self):
        """
        Return a new Candidate that is exactly like this one.
        """
        return Candidate(self.dna)

    def mutate(self, mutation_chance):
        """
        Returns a new Candidate with random genes modified based on the mutation_chance (0 to 1).
        """
        return Candidate(self.dna.mutate(mutation_chance))

    def compare(self, other):
        """
        Compares two candidates; scores closer to 0 are more similar.
        """
        return self.compare_img(other.to_image())

    def compare_img(self, other):
        diff = ImageChops.difference(self.to_image(), other)
        total = 0
        count = 0
        for (r, g, b) in diff.getdata():
            count += 3
            total = total + r + g + b
        return float(total) / float(count)


class ImageCanvas(Tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, width=256, height=256)

    def set_image(self, img):
        self.img = img
        self.tk_img = ImageTk.PhotoImage(self.img)
        self.create_image(0, 0, image=self.tk_img, anchor=Tk.NW)


class CandidateGroupFrame(Tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        target_label = Tk.Label(master, text="Target Image")
        target_label.grid(row=0, column=0)
        self.target_canvas = ImageCanvas(master)
        self.target_canvas.grid(row=1, column=0)

        parent_label = Tk.Label(master, text="Current Parent")
        parent_label.grid(row=0, column=1)
        self.parent_canvas = ImageCanvas(master)
        self.parent_canvas.grid(row=1, column=1)

        candidate_label = Tk.Label(master, text="Current Candidate")
        candidate_label.grid(row=0, column=2)
        self.candidate_canvas = ImageCanvas(master)
        self.candidate_canvas.grid(row=1, column=2)

    def set_target_image(self, img):
        self.target_canvas.set_image(img)

    def set_parent_image(self, img):
        self.parent_canvas.set_image(img)

    def set_candidate_image(self, img):
        self.candidate_canvas.set_image(img)


class App:
    def __init__(self, root, target_image_path, mutation_chance=0.1):
        self.root = root
        self.root.title("Genetic Image Matching")
        self.mutation_chance = mutation_chance

        self.candidate_group = CandidateGroupFrame(root)
        self.candidate_group.grid(row=0, column=0)

        self.parent = Candidate.random()
        self.candidate = self.parent.copy()

        self.iterations = 1
        self.generation = 1
        self.reign = 1

        # Copy the image from the filesystem to a new Image
        # to ensure the mode and size are the same as the
        # candidate images (necessary for comparison)
        orig_image = Image.open(target_image_path)
        self.target_image = Image.new('RGB', (256, 256))
        self.target_image.paste(orig_image)
        self.candidate_group.set_target_image(self.target_image)
        self.candidate_group.set_parent_image(self.parent.to_image())
        self.candidate_group.set_candidate_image(self.candidate.to_image())

        self.parent_score = self.parent.compare_img(self.target_image)
        self.candidate_score = self.candidate.compare_img(self.target_image)

        self.info = Tk.StringVar()
        self.info.set(self.get_info_text())
        self.label = Tk.Label(self.root, textvariable=self.info, anchor=Tk.W, justify=Tk.LEFT)
        self.label.grid(row=2, column=0, columnspan=3, sticky=Tk.W)

        self.chance_slider = Tk.Scale(self.root, from_=0.0, to=0.1, resolution=0.001, showvalue=0,
                                      orient=Tk.HORIZONTAL, command=self._adjust_mutation_chance)
        self.chance_slider.grid(row=3, column=0, sticky=Tk.W)
        self.chance_slider.set(self.mutation_chance)

    def iterate(self):
        self.iterations += 1
        self.reign += 1

        self.candidate = self.parent.mutate(self.mutation_chance)
        self.candidate_group.set_candidate_image(self.candidate.to_image())

        self.candidate_score = self.candidate.compare_img(self.target_image)
        # If the new score (difference) is closer to zero than the previous winner,
        # then the candidate is promoted to parent and stats updated.
        if self.candidate_score < self.parent_score:
            self._promote_candidate()

        self.info.set(self.get_info_text())
        self.root.update() # force a redraw
        self.root.after(0, self.iterate) # schedule a new iteration immediately

    def _promote_candidate(self):
        self.reign = 0
        self.generation += 1
        self.parent = self.candidate
        self.candidate_group.set_parent_image(self.parent.to_image())
        self.parent_score = self.candidate_score

    def _adjust_mutation_chance(self, val):
        self.mutation_chance = float(val)

    def get_info_text(self):
        return "\n".join([
            "Iteration: {}",
            "Generation: {}",
            "Reign: {}",
            "Best Score: {}",
            "Candidate Score: {}",
            "Mutation Chance: {}%"
        ]).format(
            self.iterations, self.generation, self.reign, self.parent_score, self.candidate_score, 100.0 * self.mutation_chance
        )

    def focus(self):
        # Holy cow this is hacky as hell, thanks macOS
        if platform() == 'Darwin':
            system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

    def run(self):
        self.root.after(1, self.iterate)
        self.root.mainloop()
