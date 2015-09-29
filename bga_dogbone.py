from pcbnew import *
from bga_utils import *
from math import sqrt


def make_dogbone(board, mod, bga_info, skip_outer, edge_layers):
    vias = []

    net = get_first_pad(mod).GetNet()

    via_dia = net.GetViaSize()
    isolation = net.GetClearance(None)
    dist = bga_info.spacing

    fy = sqrt((isolation+via_dia)**2-(dist/2)**2)
    fx = sqrt((isolation+via_dia)**2-fy**2)

    ofsx = fx/2
    ofsy = (dist-fy)/2

    for pad in filter(lambda p: p.GetNet().GetNodesCount() > 1, mod.Pads()):
        pad_pos = get_pad_position(bga_info, pad)
        if is_pad_outer_ring(bga_info, pad_pos, skip_outer):
            continue
        if is_edge_layer(bga_info,pad_pos,edge_layers):
            horizontal = abs(pad.GetPosition().x - bga_info.center.x) > abs(pad.GetPosition().y - bga_info.center.y)

            if horizontal:
                if (pad_pos.y-edge_layers) % 2 == 0:
                    ep = pad.GetPosition() + wxPoint(ofsx, -ofsy)
                else:
                    ep = pad.GetPosition() + wxPoint(-ofsx, ofsy)
            else:
                if (pad_pos.x-edge_layers) % 2 == 0:
                    ep = pad.GetPosition() + wxPoint(ofsy, -ofsx)
                else:
                    ep = pad.GetPosition() + wxPoint(-ofsy, ofsx)
        elif (edge_layers>0) and is_edge_layer(bga_info,pad_pos,edge_layers+1):
            horizontal = abs(pad.GetPosition().x - bga_info.center.x) > abs(pad.GetPosition().y - bga_info.center.y)

            dx = 1 if (pad.GetPosition().x - bga_info.center.x) > 0 else -1
            dy = 1 if (pad.GetPosition().y - bga_info.center.y) > 0 else -1

            if horizontal:
                ep = pad.GetPosition() + wxPoint(dx * ofsx, -dx * ofsy)
            else:
                ep = pad.GetPosition() + wxPoint(-dy * ofsy, dy * ofsx)
        else:
            dx = 1 if (pad.GetPosition().x - bga_info.center.x) > 0 else -1
            dy = 1 if (pad.GetPosition().y - bga_info.center.y) > 0 else -1
            ep = pad.GetPosition() + wxPoint(dx * bga_info.spacing / 2, dy * bga_info.spacing / 2)

        # Create track
        new_track = TRACK(board)
        new_track.SetStart(pad.GetPosition())
        new_track.SetEnd(ep)
        new_track.SetNetCode(pad.GetNetCode())
        new_track.SetLayer(pad.GetLayer())
        board.Add(new_track)
        # Create via
        new_via = VIA(board)
        new_via.SetPosition(ep)
        new_via.SetNetCode(pad.GetNetCode())
        new_via.SetDrill(pad.GetNet().GetViaDrillSize())
        new_via.SetWidth(pad.GetNet().GetViaSize())
        board.Add(new_via)
        vias.append(new_via)
    return vias


def make_dogbones(board, mod, skip_outer, edge_layers):
    info = get_bga_info(mod)
    return [info.spacing, make_dogbone(board, mod, info, skip_outer, edge_layers)]


my_board = LoadBoard("test11.kicad_pcb")
my_board.BuildListOfNets()

mod = my_board.FindModuleByReference("t.xc7.inst")

# Skip zero layers and route 6 layer quadrants with shifted vias and 1 transition layer
data = make_dogbones(my_board, mod, 0, 6)

SaveBoard("test1.kicad_pcb", my_board)
