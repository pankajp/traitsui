#------------------------------------------------------------------------------
#
#  Copyright (c) 2005, Enthought, Inc.
#  All rights reserved.
#  
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#  
#  Author: David C. Morrill
#  Date:   10/21/2004
#
#------------------------------------------------------------------------------

""" Defines the various text editors and the text editor factory, for the 
    wxPython user interface toolkit.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

import logging

import wx

from enthought.traits.api \
    import Dict, Str, Any, Bool, TraitError
    
from enthought.traits.ui.api \
    import View, Group

from enthought.traits.ui.ui_traits \
    import AView
    
from editor \
    import Editor
    
from editor_factory \
    import EditorFactory, ReadonlyEditor
    
from constants \
    import OKColor, ErrorColor, WindowColor

#-------------------------------------------------------------------------------
#  Start logging:
#-------------------------------------------------------------------------------

logger = logging.getLogger( __name__ )

#-------------------------------------------------------------------------------
#  Constants:
#-------------------------------------------------------------------------------

# Readonly text editor with view state colors:
HoverColor = wx.LIGHT_GREY
DownColor  = wx.WHITE

#-------------------------------------------------------------------------------
#  Define a simple identity mapping:
#-------------------------------------------------------------------------------

class _Identity ( object ):
    """ A simple indentity mapping.
    """
    def __call__ ( self, value ):    
        return value

#-------------------------------------------------------------------------------
#  Trait definitions:
#-------------------------------------------------------------------------------

# Mapping from user input text to other value
mapping_trait = Dict( Str, Any )

# Function used to evaluate textual user input
evaluate_trait = Any( _Identity() )

#-------------------------------------------------------------------------------
#  'ToolkitEditorFactory' class:
#-------------------------------------------------------------------------------

class ToolkitEditorFactory ( EditorFactory ):
    """ wxPython editor factory for text editors.
    """
    
    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------
    
    # Dictionary that maps user input to other values
    mapping = mapping_trait
    
    # Is user input set on every keystroke?
    auto_set = Bool( True )
    
    # Is user input set when the Enter key is pressed?
    enter_set = Bool( False )
    
    # Is multi-line text allowed?
    multi_line = Bool( True )
    
    # Is user input unreadable? (e.g., for a password)
    password = Bool( False )
    
    # Function to evaluate textual user input
    evaluate = evaluate_trait
    
    # The object trait containing the function used to evaluate user input
    evaluate_name = Str
    
    # The optional view to display when a read-only text editor is clicked:
    view = AView
    
    #---------------------------------------------------------------------------
    #  Traits view definition:    
    #---------------------------------------------------------------------------
        
    traits_view = View( [ 'auto_set{Set value when text is typed}',
                          'enter_set{Set value when enter is pressed}',
                          'multi_line{Allow multiple lines of text}',
                          '<extras>',
                          '|options:[Options]>' ] )
    
    extras = Group( 'password{Is this a password field?}' )
    
    #---------------------------------------------------------------------------
    #  'Editor' factory methods:
    #---------------------------------------------------------------------------
    
    def simple_editor ( self, ui, object, name, description, parent ):
        return SimpleEditor( parent,
                             factory     = self, 
                             ui          = ui, 
                             object      = object, 
                             name        = name, 
                             description = description )
    
    def custom_editor ( self, ui, object, name, description, parent ):
        return CustomEditor( parent,
                             factory     = self, 
                             ui          = ui, 
                             object      = object, 
                             name        = name, 
                             description = description ) 
    
    def text_editor ( self, ui, object, name, description, parent ):
        return SimpleEditor( parent,
                             factory     = self, 
                             ui          = ui, 
                             object      = object, 
                             name        = name, 
                             description = description ) 
    
    def readonly_editor ( self, ui, object, name, description, parent ):
        return ReadonlyTextEditor( parent,
                                   factory     = self, 
                                   ui          = ui, 
                                   object      = object, 
                                   name        = name, 
                                   description = description ) 
                                      
#-------------------------------------------------------------------------------
#  'SimpleEditor' class:
#-------------------------------------------------------------------------------
                               
class SimpleEditor ( Editor ):
    """ Simple style text editor, which displays a text field.
    """
    
    # Flag for window styles:
    base_style = 0
    
    # Background color when input is OK:
    ok_color = OKColor

    #---------------------------------------------------------------------------
    #  Trait definitions: 
    #---------------------------------------------------------------------------
        
    # Function used to evaluate textual user input:
    evaluate = evaluate_trait
        
    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------
        
    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        factory       = self.factory
        style         = self.base_style
        self.evaluate = factory.evaluate
        self.sync_value( factory.evaluate_name, 'evaluate', 'from' )
            
        if (not factory.multi_line) or factory.password:
            style &= ~wx.TE_MULTILINE
        
        if factory.password:
            style |= wx.TE_PASSWORD
            
        multi_line = ((style & wx.TE_MULTILINE) != 0)
        if multi_line:
            self.scrollable = True
            
        if factory.enter_set and (not multi_line):
            control = wx.TextCtrl( parent, -1, self.str_value,
                                   style = style | wx.TE_PROCESS_ENTER )
            wx.EVT_TEXT_ENTER( parent, control.GetId(), self.update_object )
        else:
            control = wx.TextCtrl( parent, -1, self.str_value, style = style )
            
        wx.EVT_KILL_FOCUS( control, self.update_object )
        
        if factory.auto_set:
           wx.EVT_TEXT( parent, control.GetId(), self.update_object )
           
        self.control = control
        self.set_tooltip()

    #---------------------------------------------------------------------------
    #  Handles the user entering input data in the edit control:
    #---------------------------------------------------------------------------
  
    def update_object ( self, event ):
        """ Handles the user entering input data in the edit control.
        """
        if (not self._no_update) and (self.control is not None):
            try:
                self.value = self._get_user_value()
                
                if self._error is not None:
                    self._error     = None
                    self.ui.errors -= 1
                    
                self.set_error_state( False )
                    
            except TraitError, excp:
                pass
        
    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------
        
    def update_editor ( self ):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        user_value = self._get_user_value()
        try:
            unequal = bool( user_value != self.value )
        except ValueError:
            # This might be a numpy array.
            unequal = True
            
        if unequal:
            self._no_update = True
            self.control.SetValue( self.str_value )
            self._no_update = False
            
        if self._error is not None:
            self._error     = None
            self.ui.errors -= 1
            self.set_error_state( False )

    #---------------------------------------------------------------------------
    #  Gets the actual value corresponding to what the user typed:
    #---------------------------------------------------------------------------
 
    def _get_user_value ( self ):
        """ Gets the actual value corresponding to what the user typed.
        """
        value = self.control.GetValue()
        try:
            value = self.evaluate( value )
        except:
            logger.exception( 'Could not evaluate %r in TextEditor' %  
                              ( value, ) )

        try:
            ret = self.factory.mapping.get( value, value )
        except TypeError:
            # The value is probably not hashable:
            ret = value

        return ret
        
    #---------------------------------------------------------------------------
    #  Handles an error that occurs while setting the object's trait value:
    #---------------------------------------------------------------------------
        
    def error ( self, excp ):
        """ Handles an error that occurs while setting the object's trait value.
        """
        if self._error is None:
            self._error     = True
            self.ui.errors += 1
            
        self.set_error_state( True )
        
    #---------------------------------------------------------------------------
    #  Returns whether or not the editor is in an error state:
    #---------------------------------------------------------------------------
    
    def in_error_state ( self ):
        """ Returns whether or not the editor is in an error state.
        """
        return (self.invalid or self._error)
        
#-------------------------------------------------------------------------------
#  'CustomEditor' class:
#-------------------------------------------------------------------------------
                               
class CustomEditor ( SimpleEditor ):
    """ Custom style of text editor, which displays a multi-line text field.
    """
    
    # Flag for window style. This value overrides the default.
    base_style = wx.TE_MULTILINE
                                     
#-------------------------------------------------------------------------------
#  'ReadonlyTextEditor' class:
#-------------------------------------------------------------------------------

class ReadonlyTextEditor ( ReadonlyEditor ):
    """ Read-only style of text editor, which displays a read-only text field.
    """
        
    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------
        
    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        super( ReadonlyTextEditor, self ).init( parent )
        
        if self.factory.view is not None:
            control = self.control
            wx.EVT_ENTER_WINDOW( control, self._enter_window )
            wx.EVT_LEAVE_WINDOW( control, self._leave_window )
            wx.EVT_LEFT_DOWN(    control, self._left_down )
            wx.EVT_LEFT_UP(      control, self._left_up )
    
    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------
        
    def update_editor ( self ):
        """ Updates the editor when the object trait changes externally to the 
            editor.
        """
        control   = self.control
        new_value = self.str_value
        
        if self.factory.password:
            new_value = '*' * len( new_value )
            
        if (self.item.resizable is True) or (self.item.height != -1.0):
            if control.GetValue() != new_value:
                control.SetValue( new_value )
                control.SetInsertionPointEnd()
                
        elif control.GetLabel() != new_value:
            control.SetLabel( new_value )

    #---------------------------------------------------------------------------
    #  Disposes of the contents of an editor:
    #---------------------------------------------------------------------------

    def dispose ( self ):
        """ Disposes of the contents of an editor.
        """
        if self.factory.view is not None:
            control = self.control
            wx.EVT_ENTER_WINDOW( control, None )
            wx.EVT_LEAVE_WINDOW( control, None )
            wx.EVT_LEFT_DOWN(    control, None )
            wx.EVT_LEFT_UP(      control, None )
        
        super( ReadonlyTextEditor, self ).dispose()
        
    #-- Private Methods --------------------------------------------------------
    
    def _set_color ( self ):
        control = self.control
        if not self._in_window:
            color = control.GetParent().GetBackgroundColour()
        elif self._down:
            color = DownColor
        else:
            color = HoverColor
        
        control.SetBackgroundColour( color )
        control.Refresh()
        
    #-- wxPython Event Handlers ------------------------------------------------
    
    def _enter_window ( self, event ):
        self._in_window = True
        self._set_color()
        
    def _leave_window ( self, event ):
        self._in_window = False
        self._set_color()
        
    def _left_down ( self, event ):
        self.control.CaptureMouse()
        self._down = True
        self._set_color()
        
    def _left_up ( self, event ):
        self._set_color()
        if not self._down:
            return
            
        self.control.ReleaseMouse()
        self._down = False
        
        if self._in_window:
            self.object.edit_traits( view   = self.factory.view, 
                                     parent = self.control )
    
