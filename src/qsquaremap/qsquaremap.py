
import sys, os, logging, operator
os.environ['QT_API'] = 'pyqt6'
from qtpy import QtWidgets, QtGui, QtCore

log = logging.getLogger('squaremap')
# log.setLevel( logging.DEBUG )


class HotMapNavigator:
    '''Utility class for navigating the hot map and finding nodes.'''

    @classmethod
    def findNode(class_, hot_map, targetNode, parentNode=None):
        '''Find the target node in the hot_map.'''
        for index, (rect, node, children) in enumerate(hot_map):
            if node == targetNode:
                return parentNode, hot_map, index
            result = class_.findNode(children, targetNode, node)
            if result:
                return result
        return None

    @classmethod
    def findNodeAtPosition(class_, hot_map, position, parent=None):
        '''Retrieve the node at the given position.'''
        for rect, node, children in hot_map:
            if rect.contains(position):
                return class_.findNodeAtPosition(children, position, node)
        return parent

    @staticmethod
    def firstChild(hot_map, index):
        '''Return the first child of the node indicated by index.'''
        children = hot_map[index][2]
        if children:
            return children[0][1]
        else:
            return hot_map[index][1]  # No children, return the node itself

    @staticmethod
    def nextChild(hotmap, index):
        '''Return the next sibling of the node indicated by index.'''
        nextChildIndex = min(index + 1, len(hotmap) - 1)
        return hotmap[nextChildIndex][1]

    @staticmethod
    def previousChild(hotmap, index):
        '''Return the previous sibling of the node indicated by index.'''
        previousChildIndex = max(0, index - 1)
        return hotmap[previousChildIndex][1]

    @staticmethod
    def firstNode(hot_map):
        '''Return the very first node in the hot_map.'''
        return hot_map[0][1]

    @classmethod
    def lastNode(class_, hot_map):
        '''Return the very last node (recursively) in the hot map.'''
        children = hot_map[-1][2]
        if children:
            return class_.lastNode(children)
        else:
            return hot_map[-1][1]  # Return the last node


class QSquareMap(QtWidgets.QWidget):
    """Construct a nested-box trees structure view"""

    highlightNode = QtCore.Signal(object, object, object)
    selectNode = QtCore.Signal(object, object, object)
    activateNode = QtCore.Signal(object, object, object)

    BackgroundColour = QtGui.QColor(128, 128, 128)
    max_depth = None
    max_depth_seen = None

    def __init__(
        self,
        parent=None,
        name='QSquareMap',
        model=None,
        adapter=None,
        labels=True,
        highlight=True,
        padding=3,
        margin=5,
        square_style=False
    ):
        """Initialise the QSquareMap

        adapter -- a DefaultAdapter or same-interface instance providing QSquareMap data api
        labels -- set to True (default) to draw textual labels within the boxes
        highlight -- set to True (default) to highlight nodes on mouse-over
        padding -- spacing within each square and its children (within the square's border)
        margin -- spacing around each square (on all sides)
        square_style -- use a more-recursive, less-linear, more "square" layout style,
        but the layout is less obvious wrt what node is "next" "previous" etc.
        """
        super(QSquareMap, self).__init__(parent)
        self.setObjectName(name)
        self.model = model
        self.padding = padding
        self.square_style = square_style
        self.margin = margin
        self.labels = labels
        self.setMouseTracking(highlight)
        self._activeNode = None
        self._selectedNode = None
        self._highlightedNode = None
        self.hot_map = []
        self.adapter = adapter or DefaultAdapter()

    def mouseMoveEvent(self, event):
        """
        Handle mouse-move event by highlighting element under mouse pointer.
        Mouse tracking should be enabled to receive this event.
        """
        node = HotMapNavigator.findNodeAtPosition(self.hot_map, event.position())
        self.setHighlightedNode(node, event.position())

    def mouseReleaseEvent(self, event):
        """Release over a given square in the map"""
        node = HotMapNavigator.findNodeAtPosition(self.hot_map, event.position())
        self.setSelectedNode(node, event.position())

    def mouseDoubleClickEvent(self, event):
        """Double click on a given square in the map"""
        node = HotMapNavigator.findNodeAtPosition(self.hot_map, event.position())
        if node:
            self.setActiveNode(node, event.position())

    def keyReleaseEvent(self, event):
        #event.Skip()
        if not self._selectedNode or not self.hot_map:
            return

        if event.key() == QtCore.Qt.Key.Key_Home.value:
            self.setSelectedNode(HotMapNavigator.firstNode(self.hot_map))
            return
        elif event.key == QtCore.Qt.Key.Key_End.value:
            self.setSelectedNode(HotMapNavigator.lastNode(self.hot_map))
            return

        try:
            parent, children, index = HotMapNavigator.findNode(
                self.hot_map, self._selectedNode
            )
        except TypeError:
            log.info('Unable to find hot-map record for node %s', self._selectedNode)
        else:
            if event.key() == QtCore.Qt.Key.Key_Down.value:
                self.setSelectedNode(HotMapNavigator.nextChild(children, index))
            elif event.key() == QtCore.Qt.Key.Key_Up.value:
                self.setSelectedNode(HotMapNavigator.previousChild(children, index))
            elif event.key() == QtCore.Qt.Key.Key_Right.value:
                self.setSelectedNode(HotMapNavigator.firstChild(children, index))
            elif event.key() == QtCore.Qt.Key.Key_Left.value and parent:
                self.setSelectedNode(parent)
            elif event.key() == QtCore.Qt.Key.Key_Return.value:
                self.setActiveNode(self._selectedNode, map=self)


    def activeNode(self):
        """
        Returns currently active node.

        Returns:
            Node: active node
        """
        return self._activeNode


    def setActiveNode(self, node, point=None, propagate=True):
        """
        Set given node active in the square-map.

        Args:
            node (Node):
                Node to set active.
            point (QtCore.QPointF):
                Optional; Mouse position. Defaults to None.
            propagate (bool):
                Optional; Whether the activateNode signal should be triggered. Defaults to True.

        Returns:
            None
        """
        if node == self._activeNode:
            return
        self._activeNode = node
        self.update()
        if node and propagate:
            self.activateNode.emit(node, point, self)


    def selectedNode(self):
        return self._selectedNode


    def setSelectedNode(self, node, point=None, propagate=True):
        """Set the given node selected in the square-map"""
        if node == self._selectedNode:
            return
        self._selectedNode = node
        self.update()
        if node and propagate:
            self.selectNode.emit(node, point, self)


    def highlightedNode(self):
        return self._highlightedNode


    def setHighlightedNode(self, node, point=None, propagate=True):
        """Set the currently-highlighted node"""
        if node == self._highlightedNode:
            return
        self._highlightedNode = node
        # TODO: restrict refresh to the squares for previous node and new node...
        self.update()
        if node and propagate:
            self.highlightNode.emit(node, point, self)

    def SetModel(self, model, adapter=None):
        """Set our model object (root of the tree)"""
        self.model = model
        if adapter is not None:
            self.adapter = adapter
        self.update()

    def paintEvent(self, event):
        """
        Draw the tree map on the device context.
        """
        self.painter = QtGui.QPainter(self)
        self.painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.hot_map = []
        brush = QtGui.QBrush(self.BackgroundColour)
        self.painter.setBackground(brush)
        if self.model:
            self.max_depth_seen = 0
            font = self.adapter.font_for_labels(self.painter)
            self.painter.setFont(font)
            self._em_size_ = QtGui.QFontMetrics(font).averageCharWidth()
            rect = QtCore.QRectF(event.rect())
            self.DrawBox(self.model, rect, hot_map=self.hot_map)
        self.painter.end()

    def DrawBox(self, node, rect, hot_map, depth=0):
        """Draw a model-node's box and all children nodes"""
        log.debug(
            'Draw: %s to (%s,%s,%s,%s) depth=%s',
            node, rect, depth
        )
        if self.max_depth and depth > self.max_depth:
            return
        self.max_depth_seen = max((self.max_depth_seen, depth))
        self.painter.setBrush(self.adapter.brush_for_node(node, depth, node==self._selectedNode, node==self._highlightedNode))
        self.painter.setPen(self.adapter.pen_for_node(node, depth, node==self._selectedNode))
        # drawing offset by margin within the square...
        drect = rect.adjusted(self.margin, self.margin, -self.margin, -self.margin)
        if sys.platform == 'darwin':
            # Macs don't like drawing small rounded rects...
            if rect.width() < self.padding * 2 or rect.height() < self.padding * 2:
                self.painter.drawRect(drect)
            else:
                self.painter.drawRoundedRect(drect, self.padding)
        else:
            # On modern machines, padding can be a *huge* number, far larger than
            # the dw/dh, so this reduces radius on small boxes and switches to square
            # boxes when extremely small
            pad = self.padding * 3
            if drect.width() <= pad * 2 or drect.height() <= pad * 2:
                pad = min([drect.width() // 2, drect.height() // 2])
                if pad < 1:
                    pad = 0
            if pad:
                self.painter.drawRoundedRect(drect, pad, pad)
            else:
                self.painter.drawRect(drect)
                self.DrawIconAndLabel(node, rect, depth)
        children_hot_map = []
        hot_map.append(
            (rect, node, children_hot_map)
        )

        rect = rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)

        empty = self.adapter.empty(node)
        icon_drawn = False
        if self.max_depth and depth == self.max_depth:
            self.DrawIconAndLabel(node, rect, depth)
            icon_drawn = True
        elif empty:
            # is a fraction of the space which is empty...
            log.debug('  empty space fraction: %s', empty)
            self.DrawIconAndLabel(node, rect.adjusted(0, 0, 0, (rect.height() * empty)), depth)
            icon_drawn = True
            rect.moveTop(rect.top() + rect.height() * empty)
            rect.setHeiht(rect.height() * (1.0 - empty))

        if rect.width() > self.padding * 2 and rect.height() > self.padding * 2:
            children = self.adapter.children(node)
            if children:
                log.debug('  children: %s', children)
                self.LayoutChildren(
                    children, node, rect, children_hot_map, depth + 1
                )
            else:
                log.debug('  no children')
                if not icon_drawn:
                    self.DrawIconAndLabel(node, rect, depth)
        else:
            log.debug('  not enough space: children skipped')

    def DrawIconAndLabel(self, node, rect, depth):
        '''Draw the icon, if any, and the label, if any, of the node.'''
        if rect.width() - 2 < self._em_size_ // 2 or rect.height() - 2 < self._em_size_ // 2:
            return
        self.painter.setClipRect(rect.adjusted(1, 1, -1, -1))  # Don't draw outside the box
        try:
            # TODO: draw icons
            #icon = self.adapter.icon(node, node == self._selectedNode)
            #available_sizes = icon.availableSizes(QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
            #icon_size = icon.actualSize(rect, QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
            #if icon and rect.height() >= icon.GetHeight() and w >= icon.GetWidth():
                #iconWidth = icon.GetWidth() + 2
                #self.painter.DrawIcon(icon, x + 2, y + 2)
                #icon.paint(self.painter, rect.adjusted(2, 2, 0, 0))
#
            #else:
                #iconWidth = 0
            iconWidth = 0
            if self.labels and rect.height() >= self.painter.fontMetrics().height():
                self.painter.setPen(self.adapter.color_for_label(node, depth, node == self._selectedNode))
                self.painter.drawText(rect.adjusted(iconWidth + 2, 20, 0, 0), 0, self.adapter.label(node))
        finally:
            self.painter.setClipping(False)

    def LayoutChildren(
        self, children, parent, rect, hot_map, depth=0, node_sum=None
    ):
        """Layout the set of children in the given rectangle

        node_sum -- if provided, we are a recursive call that already has sizes and sorting,
            so skip those operations
        """
        if node_sum is None:
            nodes = [(self.adapter.value(node, parent), node) for node in children]
            nodes.sort(key=operator.itemgetter(0))
            total = self.adapter.children_sum(children, parent)
        else:
            nodes = children
            total = node_sum
        if total:
            if self.square_style and len(nodes) > 5:
                # new handling to make parents with large numbers of parents a little less
                # "sliced" looking (i.e. more square)
                (head_sum, head), (tail_sum, tail) = split_by_value(total, nodes)
                if head and tail:
                    # split into two sub-boxes and render each...
                    head_coord, tail_coord = split_box(
                        head_sum / float(total), rect
                    )
                    if head_coord:
                        self.LayoutChildren(
                            head,
                            parent,
                            head_coord,
                            hot_map,
                            depth,
                            node_sum=head_sum,
                        )
                    if tail_coord and coord_bigger_than_padding(
                        tail_coord, self.padding + self.margin
                    ):
                        self.LayoutChildren(
                            tail,
                            parent,
                            tail_coord,
                            hot_map,
                            depth,
                            node_sum=tail_sum,
                        )
                    return

            (firstSize, firstNode) = nodes[-1]
            fraction = firstSize / float(total)
            head_coord, tail_coord = split_box(fraction, rect)
            if head_coord:
                self.DrawBox(
                    firstNode,
                    head_coord,
                    hot_map,
                    depth,
                )
            else:
                return  # no other node will show up as non-0 either

            if (
                len(nodes) > 1
                and tail_coord
                and coord_bigger_than_padding(tail_coord, self.padding + self.margin)
            ):
                self.LayoutChildren(
                    nodes[:-1],
                    parent,
                    tail_coord,
                    hot_map,
                    depth,
                    node_sum=total - firstSize,
                )


def coord_bigger_than_padding(tail_coord, padding):
    return tail_coord and tail_coord.width() > padding * 2 and tail_coord.height() > padding * 2


def split_box(fraction, rect):
    """
    Return set of two boxes where first is the fraction given
    """
    head, tail = None, None
    w, h = rect.width(), rect.height()

    if w >= h:
        head_w = w * fraction
        if head_w:
            head = rect.adjusted(0, 0, -(w - head_w), 0)
            tail = rect.adjusted(head_w, 0, 0, 0)
    else:
        head_h = h * fraction
        if head_h:
            head = rect.adjusted(0, 0, 0, -(h - head_h))
            tail = rect.adjusted(0, head_h, 0, 0)

    return head, tail


def split_by_value(total, nodes, headdivisor=2.0):
    """Produce, (sum,head),(sum,tail) for nodes to attempt binary partition"""
    head_sum = 0
    divider = 0
    for node in nodes[::-1]:
        if head_sum < total / headdivisor:
            head_sum += node[0]
            divider -= 1
        else:
            break
    return (head_sum, nodes[divider:]), (total - head_sum, nodes[:divider])


class DefaultAdapter:
    """Default adapter class for adapting node-trees to QSquareMap API"""

    DEFAULT_PEN = QtGui.QPen(QtCore.Qt.GlobalColor.black)
    SELECTED_PEN = QtGui.QPen(QtCore.Qt.GlobalColor.white)

    def children(self, node):
        """Retrieve the set of nodes which are children of this node"""
        return node.children

    def value(self, node, parent=None):
        """Return value used to compare nodes"""
        return node.value

    def label(self, node):
        """Return textual description of this node"""
        return str(node.name)

    def overall(self, node):
        """Calculate overall value of the node including children and empty space"""
        return sum([self.value(value, node) for value in self.children(node)])

    def children_sum(self, children, node):
        """Calculate children's total sum"""
        return sum([self.value(value, node) for value in children])

    def empty(self, node):
        """Calculate empty space as a fraction of total space"""
        overall = self.overall(node)
        if overall:
            return (overall - self.children_sum(self.children(node), node)) / float(
                overall
            )
        return 0

    def background_color(self, node, depth):
        '''The color to use as background color of the node.'''
        return None

    def foreground_color(self, node, depth):
        '''The color to use for the label.'''
        return None

    def brush_for_node(self, node, depth=0, selected=False, highlighted=False):
        """Create brush to use to display the given node"""
        if selected:
            color = QtGui.QColor(255, 0, 0)
        elif highlighted:
            color = QtGui.QColor(0, 255, 0)
        else:
            color = self.background_color(node, depth)
            if not color:
                red = (depth * 10) % 255
                green = 255 - ((depth * 5) % 255)
                blue = (depth * 25) % 255
                color = QtGui.QColor(red, green, blue)
        return QtGui.QBrush(color)

    def pen_for_node(self, node, depth=0, selected=False, highlighted=False):
        """Determine the pen to use to display the given node"""
        if selected:
            return self.SELECTED_PEN
        return self.DEFAULT_PEN

    def font_for_labels(self, painter):
        '''Return the default GUI font, scaled for printing if necessary.'''
        font = QtWidgets.QApplication.font()
        return font

    def color_for_label(self, node, depth=0, selected=False):
        """Determine the text foreground color to use to display the label of
        the given node"""
        if selected:
            fg_color = QtWidgets.QApplication.palette().highlightedText()
        else:
            fg_color = self.foreground_color(node, depth)
            if not fg_color:
                fg_color = QtWidgets.QApplication.palette().text()
        return fg_color.color()

    def icon(self, node, isSelected):
        '''The icon to display in the node.'''
        return None

    def parents(self, node):
        """Retrieve/calculate the set of parents for the given node"""
        return []


class Node:
    """Really dumb file-system node object"""

    def __init__(self, name, value, children):
        self.name = name
        self.value = value
        self.children = children

    def __repr__(self):
        return '%s( %r, %r, %r )' % (
            self.__class__.__name__,
            self.name,
            self.value,
            self.children,
        )
