# -*- coding: utf-8 -*-
"""

"""

import subprocess
import platform
import os
import numpy as np

if platform.system() == 'Linux':
    default_terminal = 'x11'
elif platform.system() == 'Darwin':
    default_terminal = 'qt'
else:
    default_terminal = 'wxt'


class Figure:
    # Plot command templates to be chained together if necessary
    _PLOT_XY_SCATTER = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}) ls {LS:d} title "{TITLE}"'
    _PLOT_XY_LINE = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}) w l ls {LS:d} title "{TITLE}"'
    _PLOT_XY_LP = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}) w lp ls {LS:d} title "{TITLE}"'
    _PLOT_XY_LP_DASHED = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}) w lp ls {LS:d} dt 3 ' \
                         'title "{TITLE}"'
    _PLOT_XY_XYERR = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}):{XE:d}:{YE:d} w xyerrorbars ' \
                     'ls {LS:d} pt -1 notitle'
    _PLOT_XY_XERR = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}):{XE:d} w xerrorbars ls {LS:d}' \
                    ' pt -1 notitle'
    _PLOT_XY_YERR = '"{FILE}" u (${X:d}*{XSCALE}):(${Y:d}*{YSCALE}):{YE:d} w yerrorbars ls {LS:d}' \
                    ' pt -1 notitle'
    _PLOT_IMG = '"{FILE}" u (($1*({XMAX}-{XMIN})/(STATS_size_x-1))+{XMIN}):' \
                '(($2*({YMAX}-{YMIN})/(STATS_size_y-1))+{YMIN}):3 matrix w image title ""'

    _SET_TITLE = 'set title "{TITLE}";'
    _SET_XRANGE = 'set xrange [{MIN}:{MAX}];'
    _SET_YRANGE = 'set yrange [{MIN}:{MAX}];'
    _SET_XLABEL = 'set xlabel "{LABEL}" offset 0,0.5;'
    _SET_YLABEL = 'set ylabel "{LABEL}" offset 1.25,0;'

    def __init__(self, datafile=None, use_default_style=False, timeout=None):
        self.__config_command = ''
        self.__user_command = ''
        self.__plot_command = ''
        self.__timeout = timeout
        self.__present_plots = 0
        self._datafile = datafile
        self._use_default_style = bool(use_default_style)
        self._font = None
        self._font_size = None
        self._title = None
        self._axis_labels = [None, None]
        self._axis_ranges = [None, None]

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, new_timeout):
        if isinstance(new_timeout, (int, float)) and new_timeout > 0:
            self.__timeout = new_timeout
        else:
            self.__timeout = None
        return

    @property
    def use_default_style(self):
        return self._use_default_style

    @use_default_style.setter
    def use_default_style(self, use_default):
        if isinstance(use_default, bool):
            self._use_default_style = use_default
        return

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, font_name):
        if isinstance(font_name, str):
            self._font = font_name.strip()
        else:
            raise TypeError('Figure.font must be of type str. Received "{0}" instead.'
                            ''.format(type(font_name)))

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, size):
        if isinstance(size, int) and size > 0:
            self._font_size = size
        else:
            raise TypeError('Figure.font_size must be of type int. Received "{0}" instead.'
                            ''.format(type(size)))

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title_str):
        if isinstance(title_str, str):
            self._title = title_str if title_str.strip() else None
        elif title_str is None:
            self._title = None
        else:
            raise TypeError('Figure.title must be of type str or None. Received "{0}" instead.'
                            ''.format(type(title_str)))

    @property
    def axis_labels(self):
        return self._axis_labels

    @axis_labels.setter
    def axis_labels(self, label_iterable):
        try:
            iterator = iter(label_iterable)
        except TypeError:
            raise TypeError('Figure.axis_labels must be an iterable. Received "{0}" instead.'
                            ''.format(type(label_iterable)))

        for axis, label in enumerate(iterator):
            if not isinstance(label, str) and label is not None:
                raise TypeError('An axis_label must be of type str or None. Received "{0}" instead.'
                                ''.format(type(label)))
            if label is None:
                self._axis_labels[axis] = None
            else:
                self._axis_labels[axis] = label if label.strip() else None
        return

    @property
    def xlabel(self):
        return self._axis_labels[0]

    @xlabel.setter
    def xlabel(self, label):
        if not isinstance(label, str) and label is not None:
            raise TypeError('An axis_label must be of type str or None. Received "{0}" instead.'
                            ''.format(type(label)))
        if label is None:
            self._axis_labels[0] = None
        else:
            self._axis_labels[0] = label if label.strip() else None
        return

    @property
    def ylabel(self):
        return self._axis_labels[1]

    @ylabel.setter
    def ylabel(self, label):
        if not isinstance(label, str) and label is not None:
            raise TypeError('An axis_label must be of type str or None. Received "{0}" instead.'
                            ''.format(type(label)))
        if label is None:
            self._axis_labels[1] = None
        else:
            self._axis_labels[1] = label if label.strip() else None
        return

    @property
    def axis_ranges(self):
        return self._axis_ranges

    @axis_ranges.setter
    def axis_ranges(self, ranges):
        try:
            iterator = iter(ranges)
        except TypeError:
            raise TypeError('Figure.axis_ranges must be an iterable. Received "{0}" instead.'
                            ''.format(type(ranges)))

        for axis, range in enumerate(iterator):
            if len(range) != 2:
                raise TypeError('An axis_range must be an iterable of length 2. Received "{0}" '
                                'instead.'.format(type(range)))
            self._axis_ranges[axis][0] = min(range)
            self._axis_ranges[axis][1] = max(range)
        return

    @property
    def xrange(self):
        return self._axis_ranges[0]

    @xrange.setter
    def xrange(self, range):
        if len(range) != 2:
            raise TypeError('An axis_range must be an iterable of length 2. Received "{0}" '
                            'instead.'.format(type(range)))
        self._axis_ranges[0][0] = min(range)
        self._axis_ranges[0][1] = max(range)
        return

    @property
    def yrange(self):
        return self._axis_ranges[1]

    @yrange.setter
    def yrange(self, range):
        if len(range) != 2:
            raise TypeError('An axis_range must be an iterable of length 2. Received "{0}" '
                            'instead.'.format(type(range)))
        self._axis_ranges[1][0] = min(range)
        self._axis_ranges[1][1] = max(range)
        return

    @property
    def datafile(self):
        return self._datafile

    @datafile.setter
    def datafile(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError('Tried to set a non-existent filepath "{0}" in Figure.datafile.'
                                    ''.format(filepath))

        num_cols = 0
        with open(filepath, 'r') as file:
            for line in file.readlines():
                if not line.startswith('#'):
                    num_cols = len(line.strip().split())
                    break
        if num_cols < 1:
            raise ValueError('0 columns detected in datafile "{0}".'.format(filepath))

        self._datafile = filepath
        return

    def user_cmd(self, cmd_str):
        if not isinstance(cmd_str, str):
            raise TypeError('Figure command must be a string. Received "{0}" instead.'
                            ''.format(type(cmd_str)))

        if not cmd_str.strip().endswith(';'):
            cmd_str += ';'

        self.__user_command += cmd_str
        return

    def user_plot_cmd(self, cmd_str):
        if not isinstance(cmd_str, str):
            raise TypeError('Figure command must be a string. Received "{0}" instead.'
                            ''.format(type(cmd_str)))

        # Reformat command
        cmd_str = cmd_str.strip().strip(';').strip(',')
        if cmd_str.startswith('plot '):
            cmd_str = cmd_str.replace('plot ', '', 1)
        elif cmd_str.startswith('replot '):
            cmd_str = cmd_str.replace('replot ', '', 1)
        cmd_str = cmd_str.strip()

        # append cmd_str to plot commands
        if self.__plot_command and not self.__plot_command.strip().endswith(','):
            self.__plot_command += ', '
        self.__plot_command += cmd_str
        print(self.__plot_command)
        return

    def _set_style(self):
        self.__config_command += 'set style line 1 lw 2 pt 7 ps 0.7 lc rgb "#1f17f4";'
        self.__config_command += 'set style line 2 lw 2 pt 5 ps 0.7 lc rgb "#ffa40e";'
        self.__config_command += 'set style line 3 lw 2 pt 9 ps 0.7 lc rgb "#ff3487";'
        self.__config_command += 'set style line 4 lw 2 pt 11 ps 0.7 lc rgb "#008b00";'
        self.__config_command += 'set style line 5 lw 2 pt 13 ps 0.7 lc rgb "#17becf";'
        self.__config_command += 'set style line 6 lw 2 pt 15 ps 0.7 lc rgb "#850085";'
        self._font = 'Helvetica'
        self._font_size = 14
        return

    def plot_xy(self, xdata_ind=0, ydata_ind=1, xerror_ind=None, yerror_ind=None, label=None,
                xscale=1, yscale=1):
        # Create configuration command string if this is the first xy plot
        if self.__present_plots == 0:
            # Clear old config command
            self.__config_command = ''

            # Apply non-default style if desired
            if not self.use_default_style:
                self._set_style()

            # command_str = 'set key outside top center horizontal box;set key width graph;'
            if self.title is not None:
                self.__config_command += self._SET_TITLE.format(TITLE=self.title)
            if self.xrange is not None:
                self.__config_command += self._SET_XRANGE.format(MIN=self.xrange[0],
                                                                 MAX=self.xrange[1])
            if self.yrange is not None:
                self.__config_command += self._SET_YRANGE.format(MIN=self.yrange[0],
                                                                 MAX=self.yrange[1])
            if self.xlabel is not None:
                self.__config_command += self._SET_XLABEL.format(LABEL=self.xlabel)
            if self.ylabel is not None:
                self.__config_command += self._SET_YLABEL.format(LABEL=self.ylabel)

        linestyle = 2 * self.__present_plots + 1
        err_linestyle = linestyle + 1

        if label is None:
            label_index = 1
            while ' title "Data {0:d}"'.format(label_index) in self.__plot_command:
                label_index += 1
            label = 'Data {0:d}'.format(label_index)

        plt_cmd = ''
        if xerror_ind is not None and yerror_ind is not None:
            plt_cmd += self._PLOT_XY_XYERR.format(FILE=self.datafile, TITLE=label, X=xdata_ind,
                                                  Y=ydata_ind, XE=xerror_ind, YE=yerror_ind,
                                                  LS=err_linestyle, XSCALE=xscale, YSCALE=yscale)
        elif xerror_ind is not None:
            plt_cmd += self._PLOT_XY_XERR.format(FILE=self.datafile, TITLE=label, X=xdata_ind,
                                                 Y=ydata_ind, XE=xerror_ind, LS=err_linestyle,
                                                 XSCALE=xscale, YSCALE=yscale)
        elif yerror_ind is not None:
            plt_cmd += self._PLOT_XY_YERR.format(FILE=self.datafile, TITLE=label, X=xdata_ind,
                                                 Y=ydata_ind, YE=yerror_ind, LS=err_linestyle,
                                                 XSCALE=xscale, YSCALE=yscale)
        else:
            plt_cmd += self._PLOT_XY_LP.format(FILE=self.datafile, TITLE=label, X=xdata_ind,
                                               Y=ydata_ind, LS=linestyle, XSCALE=xscale,
                                               YSCALE=yscale)

        if xerror_ind is not None or yerror_ind is not None:
            plt_cmd += ', '
            plt_cmd += self._PLOT_XY_LP_DASHED.format(FILE=self.datafile, TITLE=label, X=xdata_ind,
                                                      Y=ydata_ind, LS=linestyle, XSCALE=xscale,
                                                      YSCALE=yscale)

        if self.__plot_command and not self.__plot_command.strip().endswith(','):
            self.__plot_command = self.__plot_command.strip(';')
            self.__plot_command += ', '
        self.__plot_command += plt_cmd
        self.__present_plots += 1
        return

    def plot_img(self, percentile_range=None, colorbar_range=None, colorbar_label=None):
        # Clear old config command
        self.__config_command = ''

        # Apply non-default style if desired
        if not self.use_default_style:
            self._set_style()

        # command_str = 'set key outside top center horizontal box;set key width graph;'
        if self.title is not None:
            self.__config_command += self._SET_TITLE.format(TITLE=self.title)
        if self.xlabel is not None:
            self.__config_command += self._SET_XLABEL.format(LABEL=self.xlabel)
        if self.ylabel is not None:
            self.__config_command += self._SET_YLABEL.format(LABEL=self.ylabel)
        self.__config_command += 'stat "{0}" matrix u 3 nooutput;'.format(self._datafile)
        if percentile_range is not None and len(percentile_range) == 2:
            self.__config_command += 'set cbrange [{0}*STATS_min:{1}*STATS_max];'.format(
                percentile_range[0], percentile_range[1])
        elif colorbar_range is not None and len(colorbar_range) == 2:
            self.__config_command += 'set cbrange [{0}:{1}];'.format(
                colorbar_range[0], colorbar_range[1])
        else:
            self.__config_command += 'set cbrange [STATS_min:STATS_max];'
        self.__config_command += 'set format cb "%.0s%c";'
        if self.xrange is not None:
            self.__config_command += self._SET_XRANGE.format(MIN=self.xrange[0], MAX=self.xrange[1])
        if self.yrange is not None:
            self.__config_command += self._SET_YRANGE.format(MIN=self.yrange[0], MAX=self.yrange[1])
        self.__config_command += 'set xtics nomirror out;'
        self.__config_command += 'set ytics nomirror out;'
        self.__config_command += 'set size ratio -1;'
        if colorbar_label is not None:
            self.__config_command += 'set cblabel "{0}" offset 1,0;'.format('counts/s')

        plt_cmd = self._PLOT_IMG.format(FILE=self.datafile,
                                        XMIN=self.xrange[0], XMAX=self.xrange[1],
                                        YMIN=self.yrange[0], YMAX=self.yrange[1])

        if self.__plot_command and not self.__plot_command.strip().endswith(','):
            self.__plot_command = self.__plot_command.strip(';')
            self.__plot_command += ', '
        self.__plot_command += plt_cmd
        self.__present_plots += 1
        return

    def show(self):
        # set proper terminal and global font style
        if self.font and self.font_size:
            command = 'set terminal {0} font "{1},{2:d}";'.format(default_terminal,
                                                                  self.font, self.font_size)
        else:
            command = 'set terminal {0};'.format(default_terminal)
        # Append command strings config first, then user commands and then plot commands
        command += '{0};{1};plot {2};'.format(self.__config_command,
                                              self.__user_command, self.__plot_command)
        # Run process and pass command string through stdin pipe
        # The process will be persistent, so it will run until the user closes the plot window
        proc_res = subprocess.run(['gnuplot', '-p', '-e', command], shell=False,
                                  encoding='utf-8', universal_newlines=True, timeout=None,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        # Catch error from stderr and raise it
        if proc_res.returncode != 0:
            raise ChildProcessError(proc_res.stderr)
        return command

    def save_figure(self, filename='myfigure', filetype=None):
        split_name = filename.rsplit('.', 1)
        if len(split_name) != 2:
            filetype = 'png' if filetype is None else filetype
        else:
            filename = split_name[0]
            filetype = split_name[1].lower() if filetype is None else filetype.lower()

        if self.font and self.font_size:
            font_spec = ' font "{0},{1:d}"'.format(self.font, self.font_size)
        else:
            font_spec = ''
        # Set terminal according to filetype
        if filetype == 'pdf':
            command = 'set terminal pdfcairo{0};'.format(font_spec)
        elif filetype == 'png':
            command = 'set terminal pngcairo{0};'.format(font_spec)
        elif filetype == 'svg':
            command = 'set terminal svg enhanced{0};'.format(font_spec)
        else:
            raise NameError('Invalid filetype specifier "{0}". Allowed filetypes are: pdf, png and '
                            'svg.'.format(filetype))

        # Set terminal output to file to create
        filename += '.{0}'.format(filetype)
        command += 'set output "{0}";'.format(filename)
        # Append command strings config first, then user commands and then plot commands
        if self.__user_command:
            command += '{0};{1};plot {2};'.format(self.__config_command,
                                                  self.__user_command, self.__plot_command)
        else:
            command += '{0};plot {1};'.format(self.__config_command, self.__plot_command)
        # Run process and pass command string through stdin pipe
        proc_res = subprocess.run(['gnuplot', '-e', command], shell=False, encoding='utf-8',
                                  universal_newlines=True, timeout=self.__timeout,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        # Catch error from stderr and raise it
        if proc_res.returncode != 0:
            raise ChildProcessError(proc_res.stderr)
        return command

    def clear(self):
        self.__config_command = ''
        self.__plot_command = ''
        self.__user_command = ''
        self.__present_plots = 0
        self._font = None
        self._font_size = None
        self._title = None
        self._axis_labels = [None, None]
        self._axis_ranges = [None, None]
        return


if __name__ == "__main__":
    a = Figure(use_default_style=False)
    a.timeout = 10
    data = np.zeros([6, 25])
    data[0] = 2 * np.pi * np.arange(25) / 25
    data[1] = np.sin(data[0])
    data[2] = 0.5 * np.sin(data[0])
    data[3] = 2 * np.sin(data[0])
    data[4] = np.ones(len(data[0])) * 0.2 * (data[0][1]-data[0][0])
    data[5] = np.ones(len(data[0])) * 0.2
    np.savetxt('mydata.dat', data.transpose(), delimiter=' ', header='stuff\nof no concern')

    a.datafile = 'mydata.dat'
    a.title = 'My fancy plot'
    a.xlabel = 'angle (rad)'
    a.ylabel = 'amplitude'
    # a.xrange = [data[0, 0] - 0.1, data[0, -1] + 0.1]
    # a.yrange = [1.2 * data[3].min(), 1.2 * data[3].max()]

    a.plot_xy(1, 2, xerror_ind=5, yerror_ind=6, label='plottery 1')
    a.plot_xy(1, 3, xerror_ind=5, yerror_ind=6, label='plottery 2')
    a.plot_xy(1, 4, xerror_ind=5, yerror_ind=6)
    a.save_figure('testfig.png')
    a.save_figure('testfig.svg')
    a.save_figure('testfig.pdf')
    a.show()

    # a = Figure()
    # a.datafile = 'image.dat'
    # a.title = 'Confocal XY scan'
    # a.xlabel = 'X (µm)'
    # a.ylabel = 'Y (µm)'
    # a.xrange = [0, 100]
    # a.yrange = [100, 200]
    # a.plot_img(colorbar_label='counts/s')
    # a.show()
    # a.save_figure('testfig.png')
    # a.save_figure('testfig.svg')
    # a.save_figure('testfig.pdf')


