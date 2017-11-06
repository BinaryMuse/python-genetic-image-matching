import random

NUM_VERTICIES = 3
NUM_STRANDS = 50
HEADER_BYTES = 4
BYTES_PER_STRAND = 5 + 2 * NUM_VERTICIES
TOTAL_BYTES = HEADER_BYTES + BYTES_PER_STRAND * NUM_STRANDS


def randbyte():
    return random.randint(0, 255)


class Dna:
    def __init__(self, copyfrom=None):
        if copyfrom is not None:
            self.bytes = bytearray(copyfrom)
        else:
            self.bytes = bytearray(TOTAL_BYTES)

    @classmethod
    def random(cls):
        """
        Generate a random string of DNA
        """
        dna = cls()
        w = dna.get_writer()

        # Header: 4 bytes: number of verticies, per shape, and BG color (R, G, and B).
        # Shapes: 5 + 2 * n bytes: 2 * n bytes for the verticies,
        #         4 for the shape color and alpha, and 1 for the draw order.
        w.write(NUM_VERTICIES)
        w.write(randbyte()) # red
        w.write(randbyte()) # green
        w.write(randbyte()) # blue

        for i in range(NUM_STRANDS):
            w.write(randbyte()) # red
            w.write(randbyte()) # green
            w.write(randbyte()) # blue
            w.write(randbyte()) # alpha
            w.write(randbyte()) # draw order
            for j in range(NUM_VERTICIES):
                w.write(randbyte()) # x
                w.write(randbyte()) # y

        # Make sure we wrote the right number of bytes
        assert w.bytes_written() == TOTAL_BYTES

        return dna

    def get_bytes(self):
        return self.bytes

    def get_writer(self):
        return DnaWriter(self)

    def get_reader(self):
        return DnaReader(self)

    def write_byte(self, index, byte):
        self.bytes[index] = byte

    def read_byte(self, index):
        return self.bytes[index]

    def duplicate(self):
        return Dna(copyfrom=self.bytes)

    def mutate(self, mutation_chance):
        """
        Returns a new string of DNA generated by taking this DNA and randomly mutating it.
        Each gene (bit) has a chance of being mutated based on `mutation_chance`, which should
        be a number between 0 (no genes mutated) and 1 (every gene mutated).
        """
        assert mutation_chance >= 0 and mutation_chance <= 1
        copy = self.duplicate()
        for index, byte in enumerate(copy.get_bytes()):
            if index is 0:
                # Don't modify the number of verticies per shape at runtime
                # as it necessitates a change in the length of the DNA string
                continue

            if random.random() <= mutation_chance:
                shift_amount = random.randint(0, 7)
                new_byte = byte ^ (1 << shift_amount)
                copy.write_byte(index, new_byte)

        return copy

    def parse(self):
        reader = self.get_reader()
        [num_verticies] = reader.read()
        [bg_r, bg_g, bg_b] = reader.read(3)
        shapes = []
        while reader.has_more_bytes():
            [r, g, b, a, draw_order] = reader.read(5)
            verticies = []
            for i in range(num_verticies):
                [x, y] = reader.read(2)
                verticies.append((x, y))
            shapes.append({"color": (r, g, b, a), "verticies": verticies, "draw_order": draw_order})

        return {
            "num_verticies": num_verticies,
            "bg": (bg_r, bg_g, bg_b),
            "shapes": shapes,
        }


class DnaWriter:
    def __init__(self, dna):
        self.dna = dna
        self.index = 0

    def write(self, byte):
        self.dna.write_byte(self.index, byte)
        self.index += 1

    def bytes_written(self):
        return self.index


class DnaReader:
    def __init__(self, dna):
        self.dna = dna
        self.index = 0

    def read(self, num=1):
        result = []
        for i in range(num):
            result.append(self.dna.read_byte(self.index))
            self.index += 1
        return result

    def bytes_read(self):
        return self.index

    def has_more_bytes(self):
        return self.index < len(self.dna.get_bytes())
