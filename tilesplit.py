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

	def crop_region(self, xp1, yp1, xp2, yp2):
		# xp, yp = self.tile_coord_to_pixel_coord(xt, yt)
		return self.image[yp1:yp2+1, xp1:xp2+1]


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
			# print(x, y, path_prepend + "tile_" + str(counter) + ".png")
			imageio.imsave(path_prepend + "tile_" + str(counter) + ".png", input_image.crop_tile(x, y), "png")
			counter += 1


def crop_regions(tilesheet: TileSheet, path_prepend: pathlib.Path, regions: typing.Tuple[typing.Tuple[typing.Tuple[int, int, int, int], str]], verbose):
	for region in regions:
		coords = region[0]
		tempname = region[1]
		split_path = pathlib.Path(tempname).parts
		temp_path = str(pathlib.Path(path_prepend).resolve())
		subfolder = split_path[0:-1]
		for folder in subfolder:
			temp_path = pathlib.Path(temp_path).resolve() / folder
			if not temp_path.exists():
				temp_path.mkdir()
		if tempname == "_blank_":
			filename = str(path_prepend / "region_" / str(coords[0]) / "_" / str(coords[1]) / "__" / str(coords[2]) / "_" / str(coords[3])).with_suffix(".png")
			if verbose:
				print("filename", filename)
				log.write("filename " + str(filename) + "\n")
			imageio.imsave(filename, tilesheet.crop_region(*coords), "png")
		elif tempname == "_noexport_":
			pass
		else:
			filename = str((path_prepend / tempname).with_suffix(".png"))
			if verbose:
				print("filename", filename)
				log.write("filename " + str(filename) + "\n")
			# print(filename, coords)
			imageio.imsave(filename, tilesheet.crop_region(*coords), "png")


def crop_with_names(image_src: str, scale: int, verbose, names: tuple, empty: typing.Optional[str] = None, regions: typing.Optional[typing.Tuple[typing.Tuple[typing.Tuple[int, int, int, int], str]]] = None):
	input_image = TileSheet(imageio.imread(image_src, "png"), scale)
	# counter = 0
	path_prepend = pathlib.Path(image_src).resolve().parent / pathlib.Path(str(pathlib.Path(image_src).name).split(".")[0])
	try:
		os.makedirs(str(path_prepend))
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
	# print(names)
	for y in range(0, input_image.image.shape[0] // scale):
		for x in range(0, input_image.image.shape[1] // scale):
			if verbose:
				print(x, y, str((path_prepend / "tile_" / str(x) / "_" / str(y)).with_suffix(".png")))
				log.write(str(x) + str(y) + str((path_prepend / "tile_" / str(x) / "_" / str(y)).with_suffix(".png")) + "\n")
			tempname = names[y][x]
			split_path = pathlib.Path(tempname).parts
			temp_path = str(pathlib.Path(path_prepend).resolve())
			subfolder = split_path[0:-1]
			for folder in subfolder:
				temp_path = pathlib.Path(temp_path).resolve() / folder
				if not temp_path.exists():
					temp_path.mkdir()
			if verbose:
				print("tempname", tempname)
				log.write("tempname " + str(tempname) + "\n")
			if empty is not None and input_image.crop_tile(x, y).max() == 0:
				if empty == "_blank_":
					filename = pathlib.Path(str(path_prepend) + "tile_" + str(x) + "_" + str(y)).with_suffix(".png")
					if verbose:
						print("filename", filename)
						log.write("filename " + str(filename) + "\n")
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
				elif empty == "_noexport_":
					pass
				else:
					filename = str((path_prepend / empty).with_suffix(".png"))
					if verbose:
						print("filename", filename)
						log.write("filename " + str(filename) + "\n")
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
			else:
				if tempname == "_blank_":
					filename = pathlib.Path(str(path_prepend) + "tile_" + str(x) + "_" + str(y)).with_suffix(".png")
					if verbose:
						print("filename", filename)
						log.write("filename " + str(filename) + "\n")
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
				elif tempname == "_noexport_":
					pass
				else:
					filename = str((path_prepend / tempname).with_suffix(".png"))
					if verbose:
						print("filename", filename)
						log.write("filename " + str(filename) + "\n")
					imageio.imsave(filename, input_image.crop_tile(x, y), "png")
	crop_regions(input_image, path_prepend, regions, verbose)


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


def process_template(names, templates) -> typing.Tuple[typing.Tuple[int, int, str]]:
	out_list = []
	for i, line in enumerate(names.split("\n")):
		# print(line)
		if len(line) <= 1:
			continue
		elif line[0] in "!#/%-;\" ":
			continue
		elif line.startswith("end"):
			print(f"line {i+1} starting with end must be `end template`, not {line}. ending template block.")
			log.write(f"line {i+1} starting with end must be `end template`, not {line}. ending template block.\n")
			break
		elif line.startswith("template"):
			# print(f"meta template call {line}")
			line_split = line.split(" ")
			# print(line_split)
			try:
				if len(line_split) > 5:
					append = line_split[5]
				else:
					append = ""
				# expand_template(out_array, templates[line_split[1]], (int(line_split[2]), int(line_split[3])), line_split[4], append, verbose)
				for item in templates[line_split[1]]:
					out_list.append((item[0] + int(line_split[2]), item[1] + int(line_split[3]), str(line_split[4] + item[2] + append)))
			except KeyError:
				print(f"ERROR: template {line_split[1]} is undefined")
				log.write(f"ERROR: template {line_split[1]} is undefined\n")
		elif line.startswith("region"):
			out_list.append(line)
			# print("appending region: ", line)
			# line_split = line.split(" ")
			# try:
			# 	if len(line_split) > 5:
			# 		append = line_split[5]
			# 	else:
			# 		append = ""
			# 	# region_calls.append((regions[line_split[1]], (int(line_split[2]), int(line_split[3])), line_split[4], append))
			# 	region_list.extend(expand_region(regions[line_split[1]], (int(line_split[2]) * scale, int(line_split[3]) * scale), line_split[4], append, verbose))
			# except KeyError:
			# 	print(f"ERROR: region {line_split[1]} is undefined")
			# 	log.write(f"ERROR: region {line_split[1]} is undefined\n")
		else:
			line_split = line.split(" ")
			out_list.append((int(line_split[0]), int(line_split[1]), str(line_split[2])))
	# print(out_list)
	return tuple(out_list)


def clip(i: int, l: int, u: int) -> int:
	if i < l:
		i = l
	elif i > u:
		i = u
	return i


def process_region(names, x, y) -> typing.Tuple[typing.Tuple[int, int, int, int, str]]:
	out_list = []
	# print(x, y)
	for i, line in enumerate(names.split("\n")):
		# print(line)
		if len(line) <= 1:
			continue
		elif line[0] in "!#/%-;\" ":
			continue
		elif line.startswith("end"):
			print(f"line {i+1} starting with end must be `end region`, not {line}. ending region block.")
			log.write(f"line {i+1} starting with end must be `end region`, not {line}. ending region block.\n")
			break
		else:
			line_split = line.split(" ")
			# print(line_split)
			# value = (clip(int(line_split[0]), 0, x), clip(int(line_split[1]), 0, y), clip(int(line_split[2]), 0, x), clip(int(line_split[3]), 0, y))
			# print(value)
			out_list.append((clip(int(line_split[0]), 0, x), clip(int(line_split[1]), 0, y), clip(int(line_split[2]), 0, x), clip(int(line_split[3]), 0, y), str(line_split[4])))
	# print(out_list)
	return tuple(out_list)


def template_to_string(template):
	# for pretty-printing
	sb = []
	for item in template:
		for i in item:
			sb.append(str(i))
	return " ".join(sb)


def expand_template(name_array, template, offset, prepend, append, verbose, regions, region_list, scale):
	if verbose:
		print(f"expanding template\n{template_to_string(template)}\nwith offset {offset}, prepend {prepend}, and append {append}")
		log.write(f"expanding template\n{template_to_string(template)}\nwith offset {offset}, prepend {prepend}, and append {append}\n")
	for item in template:
		try:
			if item.startswith("region"):
				line_split = item.split(" ")
				try:
					if len(line_split) > 5:
						region_append = line_split[5]
					else:
						region_append = ""
					# region_calls.append((regions[line_split[1]], (int(line_split[2]), int(line_split[3])), line_split[4], append))
					# print(prepend, line_split[4], region_append, append)
					region_list.extend(expand_region(regions[line_split[1]], ((int(line_split[2]) + offset[0]) * scale, (int(line_split[3]) + offset[1]) * scale), prepend + line_split[4], region_append + append, verbose))
				except KeyError:
					print(f"ERROR: region {line_split[1]} is undefined")
					log.write(f"ERROR: region {line_split[1]} is undefined\n")
			# else:
			# 	print(item)
		except AttributeError:
			try:
				name_array[(item[1] + offset[1]) % len(name_array)][(item[0] + offset[0]) % len(name_array[0])] = prepend + item[2] + append
			except TypeError:
				print("!!! TypeError:", item)
	return name_array


def expand_region(region, offset, prepend, append, verbose) -> typing.Tuple[typing.Tuple[typing.Tuple[int, int, int, int], str]]:
	regions = []
	if verbose:
		print(f"expanding region\n{template_to_string(region)}\nwith offset {offset}, prepend {prepend}, and append {append}")
		log.write(f"expanding region\n{template_to_string(region)}\nwith offset {offset}, prepend {prepend}, and append {append}\n")
	for item in region:
		# print(item)
		# print(offset)
		coords = (int(item[0] + offset[0]), int(item[1] + offset[1]), int(item[2] + offset[0]), int(item[3] + offset[1]))
		# print(coords)
		# print()
		regions.append((coords, str(prepend + item[4] + append)))
		# region_list[(item[1] + offset[1]) % len(region_list)][(item[0] + offset[0]) % len(region_list[0])] = prepend + item[2] + append
	# print(region_list)
	return tuple(regions)


def expand_names(names, dimensions_in_tiles: typing.Tuple[int], scale, verbose)\
		-> typing.Tuple[np.ndarray, typing.Optional[str], typing.Tuple[typing.Tuple[typing.Tuple[int, int, int, int], str]]]:
	out_array = np.ndarray((dimensions_in_tiles[0] // scale, dimensions_in_tiles[1] // scale), object)
	# x = 0
	# y = 0
	swap = False
	empty = None
	template = False
	template_buffer = []
	templates = {}
	template_calls = []
	template_name = ""
	region = False
	region_x = 0
	region_y = 0
	region_buffer = []
	regions = {}
	region_calls = []
	region_name = ""
	region_list: typing.List[typing.Tuple[typing.Tuple[int, int, int, int], str]] = []
	for iy in range(0, dimensions_in_tiles[0] // scale):
		for ix in range(0, dimensions_in_tiles[1] // scale):
			out_array[iy][ix] = "_blank_"
	for i, line in enumerate(names.split("\n")):
		if len(line) <= 1:
			continue
		elif line.startswith("image") or line.startswith("verbose") or line.startswith("size"):
			continue
		elif not template and (line[0] in "!#/%-;\" "):
			continue
		elif not template and (line.startswith("default") or line.startswith("def")):
			line_split = line.split(" ")
			for iy in range(0, dimensions_in_tiles[0] // scale):
				for ix in range(0, dimensions_in_tiles[1] // scale):
					out_array[iy][ix] = line_split[1]
		elif not template and (line.startswith("empty")):
			empty = line.split(" ")[1]
		elif not template and (line.startswith("swapxy")):
			swap ^= True
		elif line.startswith("new template"):
			template = True
			template_name = line.split(" ")[2]
		elif line.startswith("end template"):
			if verbose:
				print(template_buffer)
				log.write(str(template_buffer) + "\n")
			templates[template_name] = tuple(process_template("\n".join(template_buffer), templates))
			template_buffer = []
			# print(templates)
			template = False
		elif line.startswith("template"):
			if template:
				template_buffer.append(line)
				continue
			line_split = line.split(" ")
			try:
				if len(line_split) > 5:
					append = line_split[5]
				else:
					append = ""
				expand_template(out_array, templates[line_split[1]], (int(line_split[2]), int(line_split[3])), line_split[4], append, verbose, regions, region_list, scale)
			except KeyError:
				print(f"ERROR: template {line_split[1]} is undefined")
				log.write(f"ERROR: template {line_split[1]} is undefined\n")
		elif line.startswith("final template"):
			if template:
				template_buffer.append(line)
				continue
			line_split = line.split(" ")
			try:
				if len(line_split) > 6:
					append = line_split[6]
				else:
					append = ""
				template_calls.append((templates[line_split[2]], (int(line_split[3]), int(line_split[4])), line_split[5], append))
			except KeyError:
				print(f"ERROR: template {line_split[2]} is undefined")
				log.write(f"ERROR: template {line_split[2]} is undefined\n")
		elif line.startswith("new region"):
			region = True
			line_split = line.split(" ")
			region_name = line_split[4]
			region_x = int(line_split[2])
			region_y = int(line_split[3])
		elif line.startswith("end region"):
			if verbose:
				print(region_buffer)
				log.write(str(region_buffer) + "\n")
			# print(region_buffer)
			regions[region_name] = tuple(process_region("\n".join(region_buffer), (region_x + 1) * scale, (region_y + 1) * scale))
			region_buffer = []
			# print(regions)
			region = False
		elif line.startswith("region"):
			if template:
				template_buffer.append(line)
				continue
			line_split = line.split(" ")
			try:
				if len(line_split) > 5:
					append = line_split[5]
				else:
					append = ""
				# region_calls.append((regions[line_split[1]], (int(line_split[2]), int(line_split[3])), line_split[4], append))
				region_list.extend(expand_region(regions[line_split[1]], (int(line_split[2]) * scale, int(line_split[3]) * scale), line_split[4], append, verbose))
			except KeyError:
				print(f"ERROR: region {line_split[1]} is undefined")
				log.write(f"ERROR: region {line_split[1]} is undefined\n")
		elif line.startswith("final region"):
			if template:
				template_buffer.append(line)
				continue
			line_split = line.split(" ")
			try:
				if len(line_split) > 6:
					append = line_split[6]
				else:
					append = ""
				region_calls.append((regions[line_split[2]], (int(line_split[3]) * scale, int(line_split[4]) * scale), line_split[5], append))
			except KeyError:
				print(f"ERROR: region {line_split[2]} is undefined")
				log.write(f"ERROR: region {line_split[2]} is undefined\n")
		elif line.startswith("end"):
			if region or template:
				print(f"ERROR: line {i+1} starting with end must be either `end template` or `end region`, not {line}.\nclosing block")
				log.write(f"ERROR: line {i+1} starting with end must be either `end template` or `end region`, not {line}.\nclosing block\n")
				region_buffer = []
				template_buffer = []
				region = False
				template = False
			else:
				print(f"ERROR: line {i+1} starting with end must be either `end template` or `end region`, not {line}.\nno open block to close")
				log.write(f"ERROR: line {i+1} starting with end must be either `end template` or `end region`, not {line}.\nno open block to close\n")
		elif region:
			region_buffer.append(line)
		elif template:
			template_buffer.append(line)
		# elif line.startswith("end"):
		# 	print(f"line starting with end must be either `end template` or `end region`, not {line}. exiting")
		# 	sys.exit()
		else:
			# print(line)
			# print("<3>", line)
			# print("<xy>", x, y)
			# print(line.split(" "))
			# print(line.split(" ")[2])
			line_split = line.split(" ")
			if swap:
				out_array[int(line_split[0])][int(line_split[1])] = line_split[2]
			else:
				out_array[int(line_split[1])][int(line_split[0])] = line_split[2]
			# if x > dimensions_in_tiles[1]:
			# 	x = 0
			# 	y += 1
	for call in template_calls:
		expand_template(out_array, call[0], call[1], call[2], call[3], verbose, regions, region_list, scale)
	for call in region_calls:
		region_list.extend(expand_region(call[0], call[1], call[2], call[3], verbose))
	return out_array, empty, tuple(region_list)


def delist(x):
	try:
		return x[0]
	except IndexError or TypeError:
		return x


def processTSN(tsn_path: str):
	log.write("processing tsn\n")
	with open(tsn_path, "r") as tsn_file:
		tsn_data = tsn_file.read()
	initial = tsn_data.split("\n", 6)
	if initial[0].startswith("image"):
		image_path = initial[0].split("image ")[1]  # .replace(" ", "\\ ")
		# print(image_path)
		base_path = pathlib.Path(tsn_path).resolve().parent
		# export_path = base_path / pathlib.Path(str(pathlib.Path(tsn_path).name).split(".")[0])
		# if image_path.startswith("/") or image_path[1] == ":":  # should catch filenames on windows that start with "C:/whatever" or "D:/whatever"
		if pathlib.Path(image_path).is_absolute():
			# print("absolute")
			resolved_image = pathlib.Path(image_path).resolve()
		else:
			# print("local")
			resolved_image = base_path / image_path
			# print(resolved_image)
		# print(export_path)
		# print(base_path)
		log.write(f"{base_path}\n")
		# print(resolved_image)
		log.write(f"{image_path}\n")
		# log.write(f"{export_path}\n")
		log.write(f"{resolved_image}\n")
		verbose = False
		tile_size = 0
		# if (len(sys.argv) >= 5) and sys.argv[4] in ["verbose", "-v", "--verbose", "-verbose", "--v", "true", "yes", "logging", "log", "y"]:
		# 	verbose = True
		for i, line in enumerate(initial):
			if line.startswith("verbose") and "true" in line:
				verbose = True
			try:
				if line.startswith("size") and " " in line:
					line_split = line.split(" ")[1]
					if line_split[0] in "0123456789":
						tile_size = int(line_split)
			except IndexError and TypeError and ValueError:
				print(f"ERROR: line {i} in tsn file starts with 'size' but does not correctly list a size.\nexpected a line like `size 16`, not {line}\nprogram closing...")
				log.write(f"ERROR: line {i} in tsn file starts with 'size' but does not correctly list a size.\nexpected a line like `size 16`, not {line}\nprogram closing...\n")
				sys.exit(1)
		if tile_size < 1:
				print(f"ERROR: tile size {tile_size} is not valid\nprogram closing...")
				log.write(f"ERROR: tile size {tile_size} is not valid\nprogram closing...\n")
				sys.exit(1)
		image = imageio.imread(resolved_image, "png")
		if (image.shape[0] % tile_size != 0) or (image.shape[1] % tile_size != 0):
			print(f"ERROR: image dimensions are not an integer multiple of the tile size {tile_size}, \
			tile coordinates may not work as intended")
			log.write(f"ERROR: image dimensions are not an integer multiple of the tile size {tile_size}, \
			tile coordinates may not work as intended\n")
			ask = input("Continue? [y/N]: ").lower() + " "
			if ask.startswith("y"):
				crop_with_names(resolved_image, tile_size, verbose, *expand_names(tsn_data, image.shape, tile_size, verbose))
			else:
				pass
		else:
			crop_with_names(resolved_image, tile_size, verbose, *expand_names(tsn_data, image.shape, tile_size, verbose))
	else:
		print(f"ERROR: malformed tsn file, no image path declaration in first line, instead found\n{initial[0]}\nprogram closing...")
		log.write(f"ERROR: malformed tsn file, no image path declaration in first line, instead found\n{initial[0]}\nprogram closing...\n")
		sys.exit(1)


# print(sys.argv)
with open(str((pathlib.Path(__file__).parent / "tilesplit_log.txt").resolve()), "w+") as log:
	# log.write(os.getcwd())
	# log.write("\n")
	# log.write(__file__)
	log.write("log created\n")
	log.write(f"{len(sys.argv)} arguments passed in\n")
	for item in sys.argv:
		log.write(f"{item}\n")
	if len(sys.argv) == 2:  #automatic, named
		print("reading tsn\n")
		log.write("reading tsn\n")
		if sys.argv[1].endswith(".tsn"):  # TileSplit Naming (file)
			processTSN(sys.argv[1])
		else:
			print("filetype unsupported")
	elif len(sys.argv) == 3:  # manual, unnamed
		print("splitting with no names")
		log.write("splitting with no names\n")
		crop_all(sys.argv[1], int(sys.argv[2]))
	elif len(sys.argv) >= 4:  # manual, named
		print("reading txt and cli args")
		log.write("reading txt and cli args\n")
		with open(sys.argv[3], "r") as namelist:
			# print(namelist.read())
			# print("---")
			# namelist.seek(0, 0)
			# print(expand_names(namelist.read(), imageio.imread(sys.argv[1], "png").shape, int(sys.argv[2])))
			verbose = False
			if (len(sys.argv) >= 5) and sys.argv[4] in ["verbose", "-v", "--verbose", "-verbose", "--v", "true", "yes", "logging", "log", "y"]:
				verbose = True
			tile_size = int(sys.argv[2])
			image = imageio.imread(sys.argv[1], "png")
			if (image.shape[0] % tile_size != 0) or (image.shape[1] % tile_size != 0):
				print(f"ERROR: image dimensions are not an integer multiple of the tile size {tile_size}, \
				tile coordinates may not work as intended")
				log.write(f"ERROR: image dimensions are not an integer multiple of the tile size {tile_size}, \
				tile coordinates may not work as intended\n")
				ask = input("Continue? [y/N]: ").lower() + " "
				if ask.startswith("y"):
					crop_with_names(sys.argv[1], tile_size, verbose, *expand_names(namelist.read(), image.shape, tile_size, verbose))
				else:
					pass
			else:
				crop_with_names(sys.argv[1], tile_size, verbose, *expand_names(namelist.read(), image.shape, tile_size, verbose))
