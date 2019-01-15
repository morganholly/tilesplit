import imageio
import numpy as np
import pathlib
import sys
import os
import errno
import typing


class TileSheet:
	def __init__(self, image, scale: int = 16):
		if image.__class__ == str:
			self.image: np.ndarray = imageio.imread(image, "png")
		elif image.__class__ == np.ndarray:
			self.image: np.ndarray = image
		else:
			# print(image.__class__)
			self.image: np.ndarray = image
		self.scale = scale

	def tile_coord_to_pixel_coord(self, xt: int, yt: int):
		return xt * self.scale, yt * self.scale

	def pixel_coord_to_tile_coord(self, xp: int, yp: int):
		return xp // self.scale, yp // self.scale

	def crop_tile(self, xt, yt):
		xp, yp = self.tile_coord_to_pixel_coord(xt, yt)
		return self.image[yp:yp+self.scale, xp:xp + self.scale]


def crop_all(image_src: str, scale: int):
	input_image = TileSheet(imageio.imread(image_src, "png"), scale)
	counter = 0
	path_prepend = str(pathlib.Path(image_src).resolve().parent) + "/" + str(pathlib.Path(image_src).name).split(".")[0] + "/"
	try:
		os.makedirs(path_prepend)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
	for y in range(0, input_image.image.shape[0] // scale):
		for x in range(0, input_image.image.shape[1] // scale):
			print(x, y, path_prepend + "tile_" + str(counter) + ".png")
			imageio.imsave(path_prepend + "tile_" + str(counter) + ".png", input_image.crop_tile(x, y), "png")
			counter += 1


def crop_with_names(image_src: str, scale: int, names: tuple, empty: typing.Optional[str] = None):
	input_image = TileSheet(imageio.imread(image_src, "png"), scale)
	counter = 0
	path_prepend = str(pathlib.Path(image_src).resolve().parent) + "/" + str(pathlib.Path(image_src).name).split(".")[0] + "/"
	try:
		os.makedirs(path_prepend)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
	# print(names)
	for y in range(0, input_image.image.shape[0] // scale):
		for x in range(0, input_image.image.shape[1] // scale):
			# print(x, y, path_prepend + "tile_" + str(x) + "_" + str(y) + ".png")
			tempname = names[y][x]
			# print("tempname", tempname)
			if empty is not None and input_image.crop_tile(x, y).max() == 0 :
				if empty == "_blank_":
					filename = path_prepend + "tile_" + str(x) + "_" + str(y) + ".png"
					# print(filename)
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
				elif empty == "_noexport_":
					pass
				else:
					filename = path_prepend + empty + ".png"
					# print(filename)
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
			else:
				if tempname == "_blank_":
					filename = path_prepend + "tile_" + str(x) + "_" + str(y) + ".png"
					# print(filename)
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
				elif tempname == "_noexport_":
					pass
				else:
					filename = path_prepend + tempname + ".png"
					# print(filename)
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
			counter += 1


def wrap_incr(x, y, length):
	x += 1
	if x >= length - 1:
		x = 0
		y += 1
	return x, y


def expand_names_old(names, dimensions_in_tiles: typing.Tuple[int], scale) -> np.ndarray:
	out_array = np.ndarray((dimensions_in_tiles[0] // scale, dimensions_in_tiles[1] // scale), object)
	x = 0
	y = 0
	for iy in range(0, dimensions_in_tiles[0] // scale):
		for ix in range(0, dimensions_in_tiles[1] // scale):
			out_array[iy][ix] = "_blank_"
	print("between for loops")
	print(names)
	for line in names.split("\n"):
		# print(line)
		try:
			if len(line.split(" ")) == 2:
				# count
				print("<2>", line)
				print("<xy>", x, y)
				print(line.split(" "))
				quantity = int(line.split(" ")[0])
				text = line.split(" ")[1]
				if x > dimensions_in_tiles[1]:
					x = 0
					y += 1
				if quantity > 0:
					for duplicate in [text] * quantity:
						try:
							if out_array[y][x] == "_blank_":
								out_array[y][x] = duplicate
								x, y = wrap_incr(x, y, dimensions_in_tiles[1])
							else:
								print("<!>", out_array[y][x], duplicate)
						except IndexError as e:
							if "side 0" in str(e):
								pass
							elif "side 1" in str(e):
								if x > dimensions_in_tiles[1]:
									x = 0
									y += 1
								continue
				elif quantity == -1:
					while (x < dimensions_in_tiles[1] // scale) and (y < dimensions_in_tiles[0] // scale):
						if out_array[y][x] == "_blank_":
							out_array[y][x] = text
							x, y = wrap_incr(x, y, dimensions_in_tiles[1])
						else:
							print("<!>", out_array[y][x], text)
			elif len(line.split(" ")) == 3:
				# coords
				print("<3>", line)
				print("<xy>", x, y)
				print(line.split(" "))
				print(line.split(" ")[2])
				out_array[int(line.split(" ")[1])][int(line.split(" ")[0])] = line.split(" ")[2]
			else:
				# nothing
				out_array[y][x] = line
				x, y = wrap_incr(x, y, dimensions_in_tiles[1])
			if x > dimensions_in_tiles[1]:
				x = 0
				y += 1
		except ValueError as e:
			print(e)
			print(e.__traceback__)
			continue
	return out_array


def expand_names(names, dimensions_in_tiles: typing.Tuple[int], scale) -> typing.Tuple[np.ndarray, typing.Optional[str]]:
	out_array = np.ndarray((dimensions_in_tiles[0] // scale, dimensions_in_tiles[1] // scale), object)
	x = 0
	y = 0
	empty = None
	for iy in range(0, dimensions_in_tiles[0] // scale):
		for ix in range(0, dimensions_in_tiles[1] // scale):
			out_array[iy][ix] = "_blank_"
	for i, line in enumerate(names.split("\n")):
		if (line.startswith("default")) or (line.startswith("def")):
			for iy in range(0, dimensions_in_tiles[0] // scale):
				for ix in range(0, dimensions_in_tiles[1] // scale):
					out_array[iy][ix] = line.split(" ")[1]
		elif line.startswith("empty"):
			empty = line.split(" ")[1]
		else:
			# print("<3>", line)
			# print("<xy>", x, y)
			# print(line.split(" "))
			# print(line.split(" ")[2])
			out_array[int(line.split(" ")[1])][int(line.split(" ")[0])] = line.split(" ")[2]
			if x > dimensions_in_tiles[1]:
				x = 0
				y += 1
	return out_array, empty


def delist(x):
	try:
		return x[0]
	except IndexError or TypeError:
		return x


# print(sys.argv)
if len(sys.argv) == 3:
	crop_all(sys.argv[1], int(sys.argv[2]))
elif len(sys.argv) == 4:
	with open(sys.argv[3], "r") as namelist:
		# print(namelist.read())
		# print("---")
		# namelist.seek(0, 0)
		# print(expand_names(namelist.read(), imageio.imread(sys.argv[1], "png").shape, int(sys.argv[2])))
		crop_with_names(sys.argv[1], int(sys.argv[2]), *expand_names(namelist.read(), imageio.imread(sys.argv[1], "png").shape, int(sys.argv[2])))
