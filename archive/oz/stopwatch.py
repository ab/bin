#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# Copyright (C) 2008,2009,2010  Xyne
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# (version 2) as published by the Free Software Foundation.
#
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# METADATA
# Version: 2.6

import pygtk
pygtk.require('2.0')
import gtk
from gtk import EXPAND,FILL,STOCK_GO_UP,STOCK_GO_DOWN
import pango, gobject
from time import time,localtime
import commands, os, sys, re
from string import capwords

def get_conf_dir(name):
  fpath = os.getenv('XDG_CONFIG_HOME')
  if not fpath:
    fpath = os.path.join(os.getenv('HOME'), '.config')
    sys.stderr.write("error: the environment variable \"XDG_CONFIG_HOME\" is not set\nDefaulting to " + fpath + "\n")
  return os.path.join(fpath, name)


class StockImgButton(gtk.Button):
  def __init__(self,**args):
    gtk.Button.__init__(self)
    self.alignment = gtk.Alignment(xalign=0.5,yalign=0.5)
    self.img = gtk.Image()
    self.img.set_from_stock(args['icon'],gtk.ICON_SIZE_MENU)

    self.alignment.add(self.img)
    self.add(self.alignment)
    self.img.show()
    self.alignment.show()

  def change_icon(self,icon):
    self.img.set_from_stock(icon,gtk.ICON_SIZE_MENU)

class ToggleStockImgButton(StockImgButton):
  def __init__(self,**args):
    self.on_icon = args['on_icon']
    self.off_icon = args['off_icon']

    if args.has_key('on'):
      self.is_on = True
    else:
      self.is_on = False

    if args.has_key('turn_on_cmd'):
      self.turn_on_cmd = args['turn_on_cmd']
    else:
      self.turn_on_cmd = None

    if args.has_key('turn_off_cmd'):
      self.turn_off_cmd = args['turn_off_cmd']
    else:
      self.turn_off_cmd = None

    if self.is_on:
      StockImgButton.__init__(self,icon=self.on_icon)
      self.cmd_id = self.connect('clicked',self.turn_off_cmd)
    else:
      StockImgButton.__init__(self,icon=self.off_icon)
      self.cmd_id = self.connect('clicked',self.turn_on_cmd)

  def turn_on(self):
    if not self.is_on:
      self.toggle()

  def turn_off(self):
    if self.is_on:
      self.toggle()

  def toggle(self):
    self.disconnect(self.cmd_id)
    if self.is_on:
      self.change_icon(self.off_icon)
      self.cmd_id = self.connect('clicked',self.turn_on_cmd)
      self.is_on = False
    else:
      self.change_icon(self.on_icon)
      self.cmd_id = self.connect('clicked',self.turn_off_cmd)
      self.is_on = True


class TimeFieldAdjuster(gtk.Frame):
  def __init__(self,**args):
    if args.has_key('font'):
      self.font = args['font']
      del args['font']
    else:
      self.font = pango.FontDescription('monospace 10')

    if args.has_key('interval'):
      self.interval = args['interval']
      del args['interval']
    else:
      self.interval = 60

    if args.has_key('callback'):
      self.callback = args['callback']
      del args['callback']
    else:
      self.callback = None

    if args.has_key('label'):
      self.label = args['label']
      del args['label']
    else:
      self.label = None


    self.value = 0

    gtk.Frame.__init__(self,**args)
    self.set_shadow_type(gtk.SHADOW_NONE)
    self.set_label_align(1,0.5)
    if self.label != None:
      self.set_label(self.label)

    self.holder = gtk.VBox()
    self.up = StockImgButton(icon=gtk.STOCK_GO_UP)
    self.down = StockImgButton(icon=gtk.STOCK_GO_DOWN)

    self.holder.add(self.up)
    self.holder.add(self.down)
    self.add(self.holder)

    self.up.show()
    self.down.show()
    self.holder.show()

    self.up.connect("pressed",self.press_inc)
    self.up.connect("released",self.release)
    self.up.connect("leave",self.release)

    self.down.connect("pressed",self.press_dec)
    self.down.connect("released",self.release)
    self.down.connect("leave",self.release)

    self.increasing = False
    self.decreasing = False
    self.start_delay = 350
    self.repeat_delay = 100

  def press_inc(self,*args):
    self.release()
    self.increase()
    self.increasing = True
    gobject.timeout_add(self.start_delay,self.hold_inc)

  def hold_inc(self,*args):
    if self.increasing == True:
      gobject.timeout_add(self.repeat_delay,self.increase)

  def press_dec(self,*args):
    self.release()
    self.decrease()
    self.decreasing = True
    gobject.timeout_add(self.start_delay,self.hold_dec)

  def hold_dec(self,*args):
    if self.decreasing == True:
      gobject.timeout_add(self.repeat_delay,self.decrease)

  def release(self,*args):
    self.increasing = False
    self.decreasing = False

  def increase(self,*args):
    self.set_value(self.value + 1)
    return self.increasing

  def decrease(self,*args):
    self.set_value(self.value - 1)
    return self.decreasing

  def set_value(self,val):
    if val != self.value:
      self.value = val % self.interval
      if self.callback != None:
        self.callback(self.value)

class Stopwatch:
  MODES = 4
  (TIME_DISPLAY,STOPWATCH,COUNTDOWN_A,COUNTDOWN_B) = range(0,MODES)
  MODE_LABEL = ['Current Time', 'Stopwatch', 'Countdown Timer A', 'Countdown Timer B']
  ICON_DATA = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>

<svg
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   version="1.0"
   width="166.65625"
   height="166.65625"
   id="svg2">
  <defs
     id="defs4" />
  <g
     transform="translate(883.43755,-38)"
     id="layer1">
    <g
       id="g7644">
      <path
         d="m 230.21875,184.5625 20,20.125 -20,20.125 c 23.77899,0 43.09375,19.28352 43.09375,43.0625 l 20.125,20 20.125,-20 c 0,-45.99869 -37.34506,-83.31249 -83.34375,-83.3125 z"
         transform="translate(-1030.3438,-146.5625)"
         id="path7620"
         style="fill:#366994;fill-opacity:1;fill-rule:nonzero;stroke:none" />
      <path
         d="m 273.3125,267.875 c 0,23.77899 -19.28352,43.09375 -43.0625,43.09375 l -20,20.125 20,20.125 c 45.99869,0 83.31249,-37.34506 83.3125,-83.34375 l -20.125,20 -20.125,-20 z"
         transform="translate(-1030.3438,-146.5625)"
         id="path7626"
         style="fill:#ffc331;fill-opacity:1;fill-rule:nonzero;stroke:none" />
      <path
         d="m 167.03125,247.90625 -20.125,20 c 0,45.99869 37.34506,83.31249 83.34375,83.3125 l -20,-20.125 20,-20.125 c -23.77899,0 -43.09375,-19.28352 -43.09375,-43.0625 l -20.125,-20 z"
         transform="translate(-1030.3438,-146.5625)"
         id="path7628"
         style="fill:#366994;fill-opacity:1;fill-rule:nonzero;stroke:none" />
      <path
         d="m 230.21875,184.5625 c -45.99869,0 -83.31249,37.34506 -83.3125,83.34375 l 20.125,-20 20.125,20 c 0,-23.77899 19.28352,-43.09375 43.0625,-43.09375 l 20,-20.125 -20,-20.125 z"
         transform="translate(-1030.3438,-146.5625)"
         id="path7630"
         style="fill:#ffc331;fill-opacity:1;fill-rule:nonzero;stroke:none" />
    </g>
  </g>
</svg>
'''


  def delete_event(self, widget, event, data=None):
    if self.close_to_tray:
      self.toggle_visibility()
      return True
    else:
      return False

  def hide(self, widget, *args):
    widget.hide()
    return True

  def destroy(self, widget, data=None):
    gtk.main_quit()


  def __init__(self, name='pyStopwatch', display_font=pango.FontDescription('DejaVu Sans Ultra-Light 36'),
                alarm_cmd='', alarm_txt='%t', mode=None, start_in_tray=False):
    self.name = name
    self.display_font = display_font
    self.alarm_cmd = alarm_cmd
    self.alarm_txt = alarm_txt

    if mode:
      try:
        mode = int(mode)
        if 0 <= mode < self.MODES:
          self.mode = mode
      except:
        pass
    else:
      self.mode = self.TIME_DISPLAY

    self.start_in_tray = start_in_tray

    config_dir = get_conf_dir(self.name)
    self.conf = os.path.join(config_dir, self.name+'.conf')
    self.icon = os.path.join(config_dir, 'icon.svg')
    if not os.path.exists(self.icon):
      if not os.path.isdir(config_dir):
        os.makedirs(config_dir)
      f = open(self.icon, 'w')
      f.write(self.ICON_DATA)
      f.close()

    self.close_to_tray = False
    self.is_running = []
    self.hours = []
    self.mins = []
    self.secs = []
    for i in range(0,self.MODES):
      self.is_running.append(False)
      self.hours.append(0)
      self.mins.append(0)
      self.secs.append(0)

    self.load_settings()
    self.table_options = {'xoptions':FILL,'yoptions':FILL,'xpadding':0,'ypadding':0}

    # main window
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.set_position(gtk.WIN_POS_CENTER)
    self.window.set_title(self.name)
    self.window.connect("delete_event", self.delete_event)
    self.window.connect("destroy", self.destroy)

    # main container
    self.container = gtk.Table()
    self.window.add(self.container)
    self.container.show()

    # eventbox to display the context menu in the GUI
    eventbox = gtk.EventBox()
    eventbox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
    eventbox.connect('button-press-event', self.fake_context_menu)
    eventbox.show()


    # display frame (the screen)
    self.display_frame = gtk.Frame()
    self.display_frame.set_label_align(1,0.5)
    self.display_frame.show()

    self.digit_display = gtk.Label('00:00:00')
    self.digit_display.modify_font(self.display_font)
    self.display_frame.add(self.digit_display)
    self.digit_display.show()

    # adjustment
    self.adjust_box = gtk.HBox()
    self.adjust_box.show()

    self.hour = TimeFieldAdjuster(interval=24,callback=self.set_hour,label='hour')
    self.adjust_box.add(self.hour)
    self.hour.show()

    self.min = TimeFieldAdjuster(callback=self.set_min,label='min')
    self.adjust_box.add(self.min)
    self.min.show()

    self.sec = TimeFieldAdjuster(callback=self.set_sec,label='sec')
    self.adjust_box.add(self.sec)
    self.sec.show()

    # reset button (alone, for the sake of the layout)
    self.reset_button = gtk.Button(label='Reset')
    self.reset_button.connect("clicked",self.reset)
    self.reset_button.show()

    # control box (start,stop,mode,reset)
    self.control_box = gtk.HBox()
    self.control_box.show()

    self.mode_button = gtk.Button(label='Mode')
    self.control_box.add(self.mode_button)
    self.mode_button.connect("clicked",self.toggle_mode)
    self.mode_button.show()

    self.run_button = ToggleStockImgButton(off_icon=gtk.STOCK_MEDIA_PLAY,on_icon=gtk.STOCK_MEDIA_STOP,turn_on_cmd=self.start,turn_off_cmd=self.stop)
    self.control_box.add(self.run_button)
    self.run_button.show()


    eventbox.add(self.display_frame)
    self.container.attach(eventbox,1,2,0,1,**self.table_options)
    self.container.attach(self.adjust_box,0,1,0,1,**self.table_options)
    self.container.attach(self.reset_button,0,1,1,2,**self.table_options)
    self.container.attach(self.control_box,1,2,1,2,**self.table_options)

    self.window.show()
    (self.x,self.y) = self.window.get_position()

    if self.start_in_tray:
      self.window.hide()
    else:
      self.window.show()



    pixbuf = gtk.gdk.pixbuf_new_from_file(self.icon)
    self.window.set_icon(pixbuf)
    self.statusicon=gtk.status_icon_new_from_pixbuf(pixbuf)
    #self.statusicon=gtk.status_icon_new_from_stock(gtk.STOCK_MEDIA_PLAY)
    self.statusicon.connect('activate', self.toggle_visibility)
    self.statusicon.connect('popup-menu', self.context_menu)
    self.window.connect('focus-in-event', lambda *args: self.statusicon.set_blinking(False))


    self.menu = gtk.Menu()

    self.prefs = gtk.MenuItem("Preferences")
    self.menu.append(self.prefs)
    self.prefs.connect('activate',self.open_preferences)
    self.prefs.show()

    self.help = gtk.MenuItem("Help")
    self.menu.append(self.help)
    self.help.connect('activate',self.display_help)
    self.help.show()

    self.quit = gtk.MenuItem("Quit")
    self.menu.append(self.quit)
    self.quit.connect('activate',self.destroy)
    self.quit.show()

    self.is_running[self.TIME_DISPLAY] = True
    self.timeshift = 0
    self.set_mode()
    gobject.timeout_add(200,self.run)


    # preferences
    self.prefs_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    pw = self.prefs_win
    pw.connect("delete_event", self.hide)

    pw.set_position(gtk.WIN_POS_CENTER)
    pw.set_border_width(10)
    pw.list = gtk.VBox()
    pw.add(pw.list)
    pw.set_title(self.name+" Preferences")

    pw.cmd_label_box = gtk.Alignment(xalign=0)
    pw.list.add(pw.cmd_label_box)
    pw.cmd_label_box.show()

    pw.cmd_label = gtk.Label("alarm command:")
    pw.cmd_label_box.add(pw.cmd_label)
    pw.cmd_label.show()

    pw.cmd = gtk.Entry(max=0)
    pw.list.add(pw.cmd)
    pw.cmd.set_text(self.alarm_cmd)
    pw.cmd.show()

    pw.txt_label_box = gtk.Alignment(xalign=0)
    pw.list.add(pw.txt_label_box)
    pw.txt_label_box.show()

    pw.txt_label = gtk.Label("alarm text:")
    pw.txt_label_box.add(pw.txt_label)
    pw.txt_label.show()

    pw.txt = gtk.Entry(max=0)
    pw.list.add(pw.txt)
    pw.txt.set_text(self.alarm_txt)
    pw.txt.show()

    pw.font_button = gtk.Button(label=self.display_font.to_string())
    pw.font_button.connect('clicked',self.select_font)
    pw.list.add(pw.font_button)
    pw.font_button.show()

    pw.start_in_tray = gtk.CheckButton("start minimized in tray")
    if self.start_in_tray:
      pw.start_in_tray.set_active(True)
    pw.list.add(pw.start_in_tray)
    pw.start_in_tray.show()

    pw.close_to_tray = gtk.CheckButton("close to tray")
    if self.close_to_tray:
      pw.close_to_tray.set_active(True)
    pw.list.add(pw.close_to_tray)
    pw.close_to_tray.show()

    pw.button_box = gtk.HBox()
    pw.list.add(pw.button_box)
    pw.button_box.show()

    pw.appsave = gtk.Button(label='apply and save')
    pw.appsave.connect('clicked',self.appsave)
    pw.button_box.add(pw.appsave)
    pw.appsave.show()

    pw.apply = gtk.Button(label='apply only')
    pw.apply.connect('clicked',self.apply)
    pw.button_box.add(pw.apply)
    pw.apply.show()

    pw.list.show()

    # font selection dialog
    self.fontseldiag = gtk.FontSelectionDialog('Choose a font for the stopwatch digits.')
    self.fontseldiag.connect("delete_event", self.hide)
    self.fontseldiag.set_font_name(self.display_font.to_string())
    self.fontseldiag.set_preview_text("0123456789")
    self.fontseldiag.apply_button.connect('clicked',self.set_font)
    self.fontseldiag.ok_button.connect('clicked',self.set_font_and_close)
    self.fontseldiag.cancel_button.connect('clicked',self.close_font_diag)
    self.fontseldiag.apply_button.show()



  def toggle_visibility(self,*args):
    if self.window.get_property("visible"):
      (self.x,self.y) = self.window.get_position()
      self.window.hide()
    else:
      self.window.move(self.x,self.y)
      self.window.show()

  def context_menu(self, data, event_button, event_time,*args):
    self.menu.popup(None, None, None, event_button, event_time)

  def fake_context_menu(self, widget, event):
    if event.button == 3:
      self.statusicon.emit('popup-menu', 0, 0)

  def open_preferences(self,*args):
    self.prefs_win.show()

  def apply(self,*args):
    self.alarm_cmd = self.prefs_win.cmd.get_text()
    self.alarm_txt = self.prefs_win.txt.get_text()
    self.start_in_tray = self.prefs_win.start_in_tray.get_active()
    self.close_to_tray = self.prefs_win.close_to_tray.get_active()
    self.prefs_win.hide()

  def appsave(self,*args):
    self.apply(*args)
    self.save_settings(*args)

  def save_settings(self,*args):
    conf_dir = os.path.dirname(self.conf)
    if not os.path.exists(conf_dir):
      os.makedirs(conf_dir)
    f = open(self.conf, 'w')

    f.write( self.create_tag('display_font',self.display_font.to_string()) )
    f.write( self.create_tag('alarm_txt',self.alarm_txt ) )
    f.write( self.create_tag('alarm_cmd',self.alarm_cmd) )

    if self.start_in_tray:
      val = '1'
    else:
      val = '0'
    f.write( self.create_tag('start_in_tray',val) )

    if self.close_to_tray:
      val = '1'
    else:
      val = '0'
    f.write( self.create_tag('close_to_tray',val) )

    f.close()

  def create_tag(self,tag,val):
    return "<%s>%s</%s>\n" % (tag,val,tag)

  def parse_tag(self,text,tag):
    value = None
    start = text.find('<'+tag+'>')+len(tag)+2
    if start > 0:
      end = text.find('</'+tag+'>')
      if end > start:
        value = text[start:end]
    return value

  def load_settings(self,*args):
    if os.path.exists(self.conf):
      f = open(self.conf, 'r')
      text = f.read()
      f.close()

      value = self.parse_tag(text,'display_font')
      if value != None:
        self.display_font = pango.FontDescription( value )


      value = self.parse_tag(text,'alarm_cmd')
      if value != None:
        self.alarm_cmd = value

      value = self.parse_tag(text,'alarm_txt')
      if value != None:
        self.alarm_txt = value

      value = self.parse_tag(text,'start_in_tray')
      if value != None:
        self.start_in_tray = (value == '1')

      value = self.parse_tag(text,'close_to_tray')
      if value != None:
        self.close_to_tray = (value == '1')


  def select_font(self,*args):
    self.fontseldiag.show()

  def set_font(self,*args):
    self.display_font = pango.FontDescription(self.fontseldiag.get_font_name())
    self.digit_display.modify_font(self.display_font)
    #self.prefs_win.font_label.set_text("Font: "+self.display_font.to_string())
    self.prefs_win.font_button.set_label(self.display_font.to_string())

  def set_font_and_close(self,*args):
    self.set_font(*args)
    self.fontseldiag.destroy()

  def close_font_diag(self,*args):
    self.fontseldiag.hide()
    #self.fontseldiag.destroy()


  def start(self,*args):
    self.run_button.turn_on()

    if self.mode == self.STOPWATCH:
      self.stopwatch_start = int( time() - (self.hours[self.mode] * 3600 + self.mins[self.mode] * 60 + self.secs[self.mode]) )

    elif self.mode == self.COUNTDOWN_A:
      self.countdownA_end = int( time() + (self.hours[self.mode] * 3600 + self.mins[self.mode] * 60 + self.secs[self.mode]) )

    else:
      time_array = localtime(time())
      lh = time_array[3]
      lm = time_array[4]
      ls = time_array[5]
      h = self.hours[self.mode]
      m = self.mins[self.mode]
      s = self.secs[self.mode]

      if s < ls:
        s += 60
        m -= 1
      if m < lm:
        m += 60
        h -= 1

      s = s - ls
      m = m - lm
      h = h - lh

      if self.mode == self.COUNTDOWN_B:
        h = h % 24
        self.countdownB_end = int(time() + h*3600 + m*60 + s)
      elif self.mode == self.TIME_DISPLAY:
        self.timeshift = int(h*3600 + m*60 + s)

    self.is_running[self.mode] = True

  def stop(self,*args):
    self.is_running[self.mode] = False
    self.run_button.turn_off()

    if self.mode == self.COUNTDOWN_B:
      self.load_values()
    else:
      if self.mode == self.TIME_DISPLAY:
        time_array = localtime(time()+self.timeshift)
        h = time_array[3]
        m = time_array[4]
        s = time_array[5]
      else:
        str = self.digit_display.get_text()
        h = int(str[0:2])
        m = int(str[3:5])
        s = int(str[6:8])


      self.hours[self.mode] = h
      self.mins[self.mode] = m
      self.secs[self.mode] = s

      self.set_values()
    self.update_display()


  def run(self):
    if self.is_running[self.COUNTDOWN_A]:
      diffA = self.countdownA_end - time()
      if diffA <= 0:
        self.set_mode(self.COUNTDOWN_A)
        self.reset()
        self.alarm()

    if self.is_running[self.COUNTDOWN_B]:
      diffB = self.countdownB_end - time() - self.timeshift
      if diffB <= 0:
        self.set_mode(self.COUNTDOWN_B)
        self.reset()
        self.alarm()

    if self.is_running[self.mode]:
      if not self.run_button.is_on:
        self.run_button.turn_on()
      if self.mode == self.TIME_DISPLAY:
        time_array = localtime(time()+self.timeshift)
        h = time_array[3]
        m = time_array[4]
        s = time_array[5]
      else:
        if self.mode == self.STOPWATCH:
          diff = time() - self.stopwatch_start
        else:
          if self.mode == self.COUNTDOWN_A:
            diff = diffA
          else:
            diff = diffB

        diff = int(diff)
        (m,s) = divmod(diff, 60)
        (h,m) = divmod(m,60)

      self.update_display(h=h,m=m,s=s)

    return True


  def update_display(self,**args):
    if args.has_key('h'):
      h=args['h']
    else:
      h=self.hours[self.mode]

    if args.has_key('m'):
      m=args['m']
    else:
      m=self.mins[self.mode]

    if args.has_key('s'):
      s=args['s']
    else:
      s=self.secs[self.mode]

    self.digit_display.set_text("%02d:%02d:%02d" % (h,m,s))

  def reset(self,*args):
    if self.is_running[self.mode]:
      self.stop()
      self.update_display()
    if self.mode == self.TIME_DISPLAY:
      time_array = localtime()
      h = time_array[3]
      m = time_array[4]
      s = time_array[5]
      self.timeshift = 0
      self.is_running[self.mode] = True
    else:
      h = 0
      m = 0
      s = 0

    self.hour.set_value(h)
    self.min.set_value(m)
    self.sec.set_value(s)

  def set_values(self):
    self.hour.set_value( self.hours[self.mode] )
    self.min.set_value( self.mins[self.mode] )
    self.sec.set_value( self.secs[self.mode] )

  def load_values(self):
    self.hours[self.mode] = self.hour.value
    self.mins[self.mode] = self.min.value
    self.secs[self.mode] = self.sec.value

  def set_hour(self,hour):
    if not self.is_running[self.mode]:
      self.hours[self.mode]=hour
      self.update_display()

  def set_min(self,min):
    if not self.is_running[self.mode]:
      self.mins[self.mode]=min
      self.update_display()

  def set_sec(self,sec):
    if not self.is_running[self.mode]:
      self.secs[self.mode]=sec
      self.update_display()

  def get_time(self):
    time_array = localtime(time()+self.timeshift)
    h = time_array[3]
    m = time_array[4]
    s = time_array[5]
    return "%02d:%02d:%02d" % (h, m, s)

  def get_alarm_text(self):
    if self.alarm_txt[:2] == '#!':
      return commands.getoutput(self.alarm_txt[2:])
    else:
      return '%%'.join( map( lambda x: x.replace('%t', self.get_time()), self.alarm_txt.split('%%') ) )

  def alarm(self):
    self.statusicon.set_blinking(True)

    if len(self.alarm_txt) > 0:
      self.alarm_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
      self.alarm_win.set_position(gtk.WIN_POS_CENTER)
      self.alarm_win.set_border_width(15)

      self.alarm_win.label = gtk.Label(self.get_alarm_text())
      self.alarm_win.label.set_justify(gtk.JUSTIFY_CENTER)
      self.alarm_win.label.modify_font(self.display_font)
      self.alarm_win.add(self.alarm_win.label)
      self.alarm_win.label.show()

      self.alarm_win.show()

    if len(self.alarm_cmd) > 0:
      os.system(self.alarm_cmd)

  def display_help(self, w):
    help_text = commands.getoutput('man pystopwatch')

    textview = gtk.TextView()
    textview.get_buffer().set_text(help_text)
    textview.set_editable(False)
    textview.set_wrap_mode(gtk.WRAP_WORD)
    textview.set_left_margin(5)
    textview.set_right_margin(5)

    textview_window = gtk.ScrolledWindow()
    textview_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    textview_window.add(textview)

    dialog = gtk.Dialog(None,None,gtk.DIALOG_DESTROY_WITH_PARENT,('close',1))
    dialog.set_default_size(600,500)
    dialog.vbox.pack_start(textview_window,True,True,5)
    dialog.vbox.show_all()
    response = dialog.run()
    dialog.destroy()

  def set_mode(self,mode=None):
    if mode == None:
      mode = self.mode
    elif mode != self.mode:
      if 0 <= mode < self.MODES:
        self.mode = mode
    self.set_values()
    self.display_frame.set_label(self.MODE_LABEL[self.mode])
    self.update_display()
    if self.is_running[self.mode] != self.run_button.is_on:
      self.run_button.toggle()

  def toggle_mode(self,*args):
    self.mode = (self.mode+1) % self.MODES
    self.set_mode()


  def show(self,whatever=None):
    if self.colorseldlg == None:
      self.colorseldlg = gtk.ColorSelectionDialog()
    response = self.colorseldlg.run()
    self.colorseldlg.hide()


  def main(self):
    gtk.main()

if __name__ == "__main__":
  stopwatch = Stopwatch()
  stopwatch.main()
