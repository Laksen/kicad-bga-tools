from pcbnew import *


class BgaInfo:
    spacing = 0.0
    rows = 0
    columns = 0
    center = wxPoint(0,0)


def detect_spacing(module):
    is_first = True
    min_dist = 100000000000
    for pad in module.Pads():
        if is_first:
            first_pad = pad
            is_first = False
        elif first_pad.GetPosition().x != pad.GetPosition().x:
            min_dist = min(min_dist, abs(first_pad.GetPosition().x - pad.GetPosition().x))
    return min_dist


def get_first_pad(module):
    for pad in filter(lambda p: p.GetNet().GetNodesCount() > 1, module.Pads()):
        return pad
    return None


def get_bga_info(module):
    info = BgaInfo()
    info.spacing = detect_spacing(module)
    
    minx = reduce(lambda x, y: min(x, y), map(lambda x: x.GetPosition().x, module.Pads()))
    maxx = reduce(lambda x, y: max(x, y), map(lambda x: x.GetPosition().x, module.Pads()))
    miny = reduce(lambda x, y: min(x, y), map(lambda x: x.GetPosition().y, module.Pads()))
    maxy = reduce(lambda x, y: max(x, y), map(lambda x: x.GetPosition().y, module.Pads()))

    info.origin = wxPoint(minx, miny)

    info.rows = int(1+round((maxy-miny)/float(info.spacing)))
    info.columns = int(1+round((maxx-minx)/float(info.spacing)))
    
    # Assemble pad grid
    info.pad_grid = {}
    for x in range(0,info.columns):
        info.pad_grid[x] = {}
        for y in range(0,info.rows):
            info.pad_grid[x][y] = False
    for pad in module.Pads():
        xy = wxPoint(round((pad.GetPosition().x-minx)/float(info.spacing)), round((pad.GetPosition().y-miny)/float(info.spacing)))
        info.pad_grid[xy.x][xy.y] = True
    
    info.center = wxPoint(maxx* 0.5 + minx* 0.5, maxy * 0.5 + miny* 0.5)
    return info


def get_pad_position(bga_info, pad):
    offset = pad.GetPosition()-bga_info.center
    return wxPoint(int(offset.x/bga_info.spacing), int(offset.y/bga_info.spacing))+wxPoint(bga_info.columns/2, bga_info.rows/2)


def is_pad_outer_ring(bga_info, pad_pos, rows):
    return (pad_pos.x<rows) or (pad_pos.y<rows) or ((bga_info.columns-pad_pos.x)<=rows) or ((bga_info.rows-pad_pos.y)<=rows)


def is_edge_layer(bga_info, pad_pos, rows):
    return is_pad_outer_ring(bga_info,pad_pos,rows) and \
           (((pad_pos.x>=rows) and ((bga_info.columns-pad_pos.x)>rows)) !=
            ((pad_pos.y>=rows) and ((bga_info.rows-pad_pos.y)>rows)))



def get_net_classes(board, vias, except_names):
    net_list = list(set(map(lambda x: x.GetNet().GetClassName(), vias)))
    net_list = filter(lambda x: not (x in except_names), net_list)
    return filter(lambda x: x != "Default", net_list)


def get_signal_layers(board):
    return filter(lambda x: IsCopperLayer(x) and (board.GetLayerType(x)==LT_SIGNAL), board.GetEnabledLayers().Seq())


def get_all_pads(board, from_module):
    lst = list()
    for mod in board.GetModules():
        if mod != from_module:
            lst = lst + list(mod.Pads())
    return lst


def get_connection_dest(via, all_pads):
    connected_pads = filter(lambda x: x.GetNetname() == via.GetNetname(), all_pads)
    count = len(connected_pads)
    if(count == 0):
        return wxPoint(0,0)
    p = reduce(lambda x,y: x+y, map(lambda x: x.GetPosition(), connected_pads), wxPoint(0,0))
    return wxPoint(p.x/count, p.y/count)


def pos_to_local(mod_info, via):
    pos = via.GetPosition()
    ofs = pos - mod_info.center
    px = int(round(ofs.x/float(mod_info.spacing)))+mod_info.columns/2
    py = int(round(ofs.y/float(mod_info.spacing)))+mod_info.rows/2
    return wxPoint(px,py)
