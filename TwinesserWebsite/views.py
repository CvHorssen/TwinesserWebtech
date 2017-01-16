import datetime
from datetime import datetime as dt
import ns_api
from django.http import HttpResponse
from django.template import loader
from rest_framework.decorators import api_view, parser_classes

timeDict = {"0":"00","1":"01","2":"02","3":"03","4":"04","5":"05","6":"06","7":"07","8":"08","9":"09","a":10,"b":11,"c":12,"d":13,"e":14,"f":15,"g":16,"h":17,"i":18,"j":19,"k":20,"l":21,"m":22,"n":23,"o":24,"p":25,"q":26,"r":27,"s":28,"t":29,"u":30,"v":31,"w":32,"x":33,"y":34,"z":35,"A":36,"B":37,"C":38,"D":39,"E":40,"F":41,"G":42,"H":43,"I":44,"J":45,"K":46,"L":47,"M":48,"N":49,"O":50,"P":51,"Q":52,"R":53,"S":54,"T":55,"U":56,"V":57,"W":58,"X":59}
subStatuses = {
    "VOLGENS-PLAN" : "This train goes as scheduled.",
    "GEANNULEERD" : "This train has been canceled.",
    "GEWIJZIGD" : "The planning for this train changed, pay attention to the times and tracks.",
    "OVERSTAP-NIET-MOGELIJK" : "There have been some changes which make this transfer impossible.",
    "VERTRAAGD" : "This train has been delayed.",
    "NIEUW" : "This is an extra train."
}
tripStatuses = {
    "VOLGENS-PLAN" : "As scheduled.",
    "GEWIJZIGD" : "Changes detected.",
    "VERTRAAGD" : "Delays detected.",
    "NIEUW" : "Extra trains.",
    "NIET-OPTIMAAL" : "This advise is not optimal.",
    "NIET-MOGELIJK" : "There are some complications which make it impossible to take this trip.",
    "PLAN-GEWIJZIGD" : "Schedule changed."
}

# ns-api
ns_username = ""
ns_password = ""


@api_view(['GET'])
def home(request):
    context = {}
    try:
        destinationShort = request.GET['d']
        startpointShort = request.GET['s']
        time = request.GET['t']
        viaShort = None
        try:
            viaShort = request.GET['v']
        except:
            viaShort = None
        try:
            return link(destinationShort, startpointShort, time, request, viaShort)
        except Exception as ex:
            print("Something went wrong during processing of the GET variables, forwarding to index.html (probably someone was fidling with the link)")
            print(ex.args)
            print(type(ex))
            print(ex)
            template = loader.get_template('index.html')
    except Exception as ex:
        print("The required GET variables are not defined, so forwarding to index.html")
        template = loader.get_template('index.html')
    return HttpResponse(template.render(context, request))


def link(destShort, startShort, timeShort, request, viaShort):
    context = {}
    stationList = getStationByCode(startShort, destShort, viaShort)
    startLong = stationList[0]
    destLong = stationList[1]
    viaLong = stationList[2]
    timeLong = getTimeFromCode(timeShort)
    context['trips'] = []
    for trip in getRoutings(startShort, destShort, timeLong, 1, 5, viaLong):
        context['trips'].append({
            'departTime': trip.departure_time_actual.strftime("%H:%M"),
            'arrivalTime': trip.arrival_time_actual.strftime("%H:%M"),
            'status': tripStatuses[trip.status],
            'transfers': trip.nr_transfers,
            'travelTime': trip.travel_time_actual,
            'subTrips': []
        })
        tripPart = trip.trip_parts
        for subTrip in tripPart:
            context['trips'][len(context['trips']) - 1]['subTrips']. append({
                'departTime' :subTrip.stops[0].time.strftime("%H:%M"),
                'departTrack' : subTrip.stops[0].platform,
                'departStation' : subTrip.stops[0].name,
                'arrivalTime' : subTrip.stops[-1].time.strftime("%H:%M"),
                'arrivalTrack' : subTrip.stops[-1].platform,
                'arrivalStation' : subTrip.stops[-1].name,
                'status' : subStatuses[subTrip.status],
            })

    #Set all variables
    context['from'] = startLong
    context['to'] = destLong
    context['via'] = viaLong
    context['time'] = timeLong
    template = loader.get_template('tweetlink.html')
    return HttpResponse(template.render(context, request))

def getRoutings(start, end, time, pre, post, via):
    routings = []
    if (ns_password == "") | (ns_username == ""):
        print("CRITICAL WARNING: CREDENTIALS FOR NS API EMPTY.")
        return []
    try:
        ns = ns_api.NSAPI(ns_username, ns_password)
        via_string = ""
        if via is None:
            via_string = None
        else:
            via_string = "&viaStation=" + via
        routings = ns.get_trips(start=start, via=via_string, destination=end, prev_advices=pre, next_advices=post, timestamp=time)
    except Exception as inst:
        print("The connection to the NS api failed. (Trip)")
        print(type(inst))
        print(inst.args)
        print(inst)
        return []
    return routings


def getStationByCode(code1, code2, code3):
    if (ns_password == "") | (ns_username == ""):
        print("CRITICAL WARNING: CREDENTIALS FOR NS API EMPTY.")
        return ["Unknown", "Unknown"]
    try:
        try:
            ns = ns_api.NSAPI(ns_username, ns_password)
            stations = ns.get_stations()
        except:
            print("The connection to the NS api failed (station list).")

#Station 1
        i = 0
        done = False
        temp = ""
        while (not done) & (not temp == code1):
            try:
                temp = stations[i].key
                i += 1
            except:
                done = True
        i -= 1

        result = []
        result.append(stations[i].names['long'])
#Station 2
        i = 0
        done = False
        temp = ""
        while (not done) & (not temp == code2):
            try:
                temp = stations[i].key
                i += 1
            except:
                done = True
        i -= 1
        result.append(stations[i].names['long'])

#Station 3
        if code3 is not None:
            i = 0
            done = False
            temp = ""
            while (not done) & (not temp == code3):
                try:
                    temp = stations[i].key
                    i += 1
                except:
                    done = True
            i -= 1
            result.append(stations[i].names['long'])
        else:
            result.append(None)
    except:
        print("One of the codes provided does not match a station.")
        result = ["Unknown", "Unknown", "Unknown"]
    return result


def getTimeFromCode(code):
    hour = timeDict[code[0]]
    minute = timeDict[code[1]]
    return str(hour) + ":" + str(minute)