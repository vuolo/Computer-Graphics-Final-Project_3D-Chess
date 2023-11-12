import tkinter as tk
import tkinter.colorchooser as tkcolorchooser

class Slider:
    def __init__(self, root, label_text, min_value, max_value, initial_value, resolution=0.01):
        self.root = root
        self.label = tk.Label(self.root, text=label_text)
        self.label.pack(padx=10, pady=5, anchor="w")
        # Create a Tkinter Scale widget (slider)
        self.slider = tk.Scale(self.root, from_=min_value, to=max_value, orient="horizontal", resolution=resolution)
        self.slider.set(initial_value)  # Set the initial scale value
        self.slider.pack()

    def get_value(self):
        # Get the slider value
        value = self.slider.get()
        self.root.update_idletasks()
        self.root.update()
        return value

class ColorPicker:
    def __init__(self, root, label_text, initial_color=(0,0,0)):
        '''

        :param root:
        :param label_text:
        :param initial_color: tuple of 3 floats RGB between 0 and 1
        '''
        self.root = root
        self.label = tk.Label(self.root, text=label_text)
        self.label.pack(padx=10, pady=5, anchor="w")
        self.color_norm = initial_color
        self.color_255 = tuple([int(i*255) for i in self.color_norm])
        self.color_hex = self.rgb_to_hex(self.color_255)

        self.color_button = tk.Button(self.root, text="Pick a color", command=self.pick_color, background=self.color_hex)
        self.color_button.pack()

    def pick_color(self):
        color_rgb, color_hex = tkcolorchooser.askcolor()  # Get the selected color
        if color_rgb is not None:
            self.color_255 = tuple([int(i) for i in color_rgb])
            self.color_hex = color_hex
            self.color_norm = tuple([i/255 for i in color_rgb])

            self.color_button.config(background=color_hex)  # Update button color
        self.root.update_idletasks()
        self.root.update()

    def get_color(self):
        return self.color_norm

    def rgb_to_hex(self, rgb):
        """translates an rgb tuple of int to a tkinter friendly color code
        """
        return "#%02x%02x%02x" % rgb


class RadioButton:
    def __init__(self, root, label_text, options_dict, initial_option=None):
        self.root = root
        self.label = tk.Label(self.root, text=label_text)
        self.label.pack(padx=10, pady=5, anchor="w")
        if initial_option is None:
            initial_option = list(options_dict.keys())[0]

        initial_value = options_dict[initial_option]
        self.option_var = tk.StringVar(value=initial_value)

        for key, value in options_dict.items():
            self.button = tk.Radiobutton(self.root, text=key, variable=self.option_var, value=value)
            self.button.pack()


    def get_value(self):
        # get the value of the selected radio button using var.get()
        value = self.option_var.get()
        self.root.update_idletasks()
        self.root.update()
        return value


class CheckBox:
    def __init__(self, root, label_text, initial_state=False):
        self.root = root
        self.var = tk.BooleanVar(value=initial_state)
        self.checkbox = tk.Checkbutton(self.root, text=label_text, variable=self.var)
        self.checkbox.pack(padx=10, pady=5, anchor="w")

    def get_value(self):
        self.root.update_idletasks()
        self.root.update()
        return self.var.get()


class SimpleGUI:
    def __init__(self, title):
        # Create a Tkinter root window for the slider
        self.root = tk.Tk()
        self.root.title(title)

    def add_slider(self, label_text, min_value, max_value, initial_value, resolution=0.01):
        slider = Slider(self.root, label_text, min_value, max_value, initial_value, resolution)
        return slider

    def add_color_picker(self, label_text, initial_color=(0,0,0)):
        color_picker = ColorPicker(self.root, label_text, initial_color)
        return color_picker

    def add_radio_buttons(self, label_text, options_dict, initial_option=None):
        radio_button = RadioButton(self.root, label_text, options_dict, initial_option)
        return radio_button

    def add_checkbox(self, label_text, initial_state=True):
        checkbox = CheckBox(self.root, label_text, initial_state)
        return checkbox

if __name__ == '__main__':
    gui = SimpleGUI("Test GUI")

    slider = gui.add_slider(label_text="Test Slider",
                            min_value=0,
                            max_value=10,
                            initial_value=5,
                            resolution=1)

    color_picker = gui.add_color_picker(label_text="Pick a Color",
                                        initial_color=(0.9, 0.1, 0.1))
    # initial color is a tuple of 3 floats RGB between 0 and 1

    radio_button = gui.add_radio_buttons(label_text="Pick a radio button",
                                         options_dict={"option1": 1,
                                                       "option2": 2},
                                         initial_option="option1")

    checkbox = gui.add_checkbox("Enable Feature", initial_state=True)

    # warning: this is an infinite loop. You need to close the window to stop the program. Ignore the error at the end.
    while True:
        print("Slider value: ", slider.get_value())
        print("Color value: ", color_picker.get_color())
        print("Radio button value: ", radio_button.get_value())
        print("Checkbox value: ", checkbox.get_value())

