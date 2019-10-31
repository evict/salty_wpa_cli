def print_color(color, msg):

    color = lookup_color(color)

    print(f"{color}{msg}", end='\033[0m\n')


def colored_string(color, msg):

    color = lookup_color(color)
    end = '\033[0m'

    return f"{color}{msg}{end}"


def lookup_color(color):

    colors = {'red': '\033[31m',
              'bold_red': '\033[1;31m',
              'green': '\033[92m',
              'bold_green': '\033[1;92m',
              'underlined': '\033[4m'}

    return colors[color]
