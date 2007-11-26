#-------------------------------------------------------------------------------
#  
#  Defines a themed read-only text string.
#  
#  Written by: David C. Morrill
#  
#  Date: 08/11/2007
#  
#  (c) Copyright 2007 by Enthought, Inc.
#  
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

import wx

from image_slice \
    import paint_parent
    
#-------------------------------------------------------------------------------
#  Class 'ImageText'  
#-------------------------------------------------------------------------------

class ImageText ( wx.PyWindow ):
    """ Defines a text control that displays an ImageSlice in its background.
    """
    
    #-- wx.PyWindow Method Overrides -------------------------------------------
    
    def __init__ ( self, parent, theme, text = '' ): 
        """ Initializes the object.
        """
        self._theme       = theme
        self._image_slice = theme.image_slice
                                            
        super( ImageText, self ).__init__( parent, -1, 
                                           style = wx.FULL_REPAINT_ON_RESIZE )
                                           
        self._text_size = self._fill = None  
        self.SetLabel( text )
        
        # Set up the painting event handlers:
        wx.EVT_ERASE_BACKGROUND( self, self._erase_background )
        wx.EVT_PAINT( self, self._on_paint )
        
        size = self.GetMinSize()
        self.SetMinSize( size )
        self.SetSize( size )
        
    def AcceptsFocus ( self ):
        """ Indicate that we are a static control that does not accept focus.
        """
        return False
        
    #-- wxPython Event Handlers ------------------------------------------------
    
    def _erase_background ( self, event ):
        """ Do not erase the background here (do it in the 'on_paint' handler).
        """
        pass
           
    def _on_paint ( self, event ):
        """ Paint the background using the associated ImageSlice object.
        """
        dc = wx.PaintDC( self )
        if self._fill is not False:
            paint_parent( dc, self )
            
        self._fill = True
        wdx, wdy   = self.GetClientSizeTuple()
        text       = self.GetLabel()
        self._image_slice.fill( dc, 0, 0, wdx, wdy, True )
        dc.SetBackgroundMode( wx.TRANSPARENT )
        dc.SetTextForeground( self._image_slice.content_color )
        dc.SetFont( self.GetFont() )
        tx, ty, tdx, tdy = self._get_text_bounds()
        dc.DrawText( text, tx, ty )
         
    def GetMinSize ( self ):
        """ Returns the minimum size for the window.
        """
        tdx, tdy, descent, leading = self._get_text_size()
        content = self._theme.content
        tdx    += (content.left + content.right)
        tdy    += (content.top  + content.bottom)
        slice   = self._image_slice
        
        return wx.Size( max( slice.left  + slice.right,
                             slice.xleft + slice.xright  + tdx + 8 ),
                        max( slice.top   + slice.bottom,
                             slice.xtop  + slice.xbottom + tdy + 4 ) )
                        
    def SetFont ( self, font ):
        """ Set the window font.
        """
        super( ImageText, self ).SetFont( font )
        
        self._refresh()
                        
    def SetLabel ( self, label ):
        """ Set the window label.
        """
        super( ImageText, self ).SetLabel( label )
        
        self._refresh()

    def _refresh ( self ):
        """ Refreshes the contents of the control.
        """
        if self._fill is True:
            self._fill = False
        
        if self._text_size is not None:
            self.RefreshRect( wx.Rect( *self._get_text_bounds() ), False )
            self._text_size = None
            
        self.SetMinSize( self.GetMinSize() )
        self.RefreshRect( wx.Rect( *self._get_text_bounds() ), False )
        
    def _get_text_size ( self, text = None ):
        """ Returns the text size information for the window.
        """
        if self._text_size is None:
            if text is None:
                text = self.GetLabel()
                
            if text.strip() == '':
                text = 'M'
                
            self._text_size = self.GetFullTextExtent( text )
            
        return self._text_size

    def _get_text_bounds ( self ):
        """ Get the window bounds of where the current text should be
            displayed.
        """
        tdx, tdy, descent, leading = self._get_text_size()
        wdx, wdy  = self.GetClientSizeTuple()
        slice     = self._image_slice
        theme     = self._theme
        content   = theme.content
        ady       = wdy - slice.xtop - slice.xbottom
        ty        = (wdy + slice.xtop + content.top - slice.xtop - 
                           slice.xbottom - tdy) / 2
        alignment = theme.alignment
        if alignment == 'left':
            tx = slice.xleft + content.left
        elif alignment == 'center':
            adx = wdx - slice.xleft - slice.xright
            tx  = slice.xleft + content.left + 4 + ((adx - tdx) / 2)
        else:
            tx = wdx - tdx - slice.xright - content.right
          
        return ( tx + theme.label.left, ty + theme.label.top, tdx, tdy )

