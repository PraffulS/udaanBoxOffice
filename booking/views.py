from django.shortcuts import render
from booking.models import screen, seat
from django.http import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def loginView(request):
	return render(request, 'login.html')

@csrf_exempt
def home(request):
	request.session['login'] = True
	return render(request, 'home.html')

@csrf_exempt
def createScreen(request): #create screen api
	try:
		screenInfo = json.loads(request.body)
		if 'name' in screenInfo and 'seatInfo' in screenInfo:
			screenName = screenInfo['name']
			if not screen.objects.filter(screenName=screenName).exists():
				screenObj = screen()
				screenObj.screenName = screenName
				screenObj.save()
			else:
				return JsonResponse({'code':500,'message':'Screen already exists'})
			seatInfo = dict(screenInfo['seatInfo'])
			for row, rowInfo in seatInfo.items():
				numberOfSeats = int(rowInfo['numberOfSeats'])
				aisleSeats = list(rowInfo['aisleSeats'])
				for i in range(numberOfSeats):
					seatObj = seat()
					seatObj.screenId = screenObj
					seatObj.rowName = str(row)
					seatObj.seatNo = i
					if i in aisleSeats:
						seatObj.isAisle = 1
					seatObj.save()
			return JsonResponse({'code':200,'message':'screen added successfully'})
		else:
			return JsonResponse({'code':500,'message':'payload data is incorrect'})
	except Exception as e:
		return JsonResponse({'code':500,'message':'Some problem has occured.'})

@csrf_exempt
def reserveTickets(request, screen_name): #ticket reservation api
	try:	
		bookingInfo = json.loads(request.body)
		if 'seats' in bookingInfo:
			if screen.objects.filter(screenName=screen_name).exists():
				unbooked_rows = []
				screenObj = screen.objects.filter(screenName=screen_name)[0]
				seats = bookingInfo['seats']
				if not seat.objects.filter(screenId=screenObj.screenId, rowName__in=list(seats)).exists():
					return JsonResponse({'code':500,'message':'rows donot exists'})
				else:
					for row, seatNo in seats.items():
						if not seat.objects.filter(screenId=screenObj.screenId, rowName=str(row), seatNo__in=list(seatNo), status=1).exists():
							seatsObj = seat.objects.filter(screenId=screenObj.screenId, rowName=str(row), seatNo__in=list(seatNo))
							seatsObj.update(status=1)
						else:
							unbooked_rows.append(row)
					if len(unbooked_rows) > 0:
						return JsonResponse({'code':200,'message':'Unfortunately seats of rows '+str(unbooked_rows)+' cannot be booked because of unavailabilty'})
					else:
						return JsonResponse({'code':200,'message':'Seats booked successfully'})
			else:
				return JsonResponse({'code':500,'message':'Screen does not exist'})
		else:
			return JsonResponse({'code':500,'message':'payload data is incorrect'})
	except Exception as e:
		return JsonResponse({'code':500,'message':'Some problem has occured.'})

@csrf_exempt
def getAvailableSeats(request, screen_name):
	try:
		if request.GET.get('status') == 'unreserved': #get unreserved seats
			if screen.objects.filter(screenName=screen_name).exists():
				screenObj = screen.objects.filter(screenName=screen_name)[0]
				rowNames = seat.objects.filter(screenId=screenObj.screenId).values_list('rowName', flat=True).distinct() 
				unreservedSeatsDict = {}
				for row in rowNames:
					unreservedSeats = seat.objects.filter(screenId=screenObj.screenId, rowName=row, status=0).order_by('seatNo').values_list('seatNo', flat=True) 
					unreservedSeatsDict[row] = list(unreservedSeats)
				return JsonResponse({'seats': str(unreservedSeatsDict)})
			else:
				return JsonResponse({'code':500,'message':'Screen does not exist'})

		elif request.GET.get('numSeats') and request.GET.get('choice'): #get seat arrangement of desired choice
			numSeats = int(request.GET.get('numSeats'))
			choice = str(request.GET.get('choice'))
			rowChoice = choice[0]
			seatNo = int(choice[1:])
			if screen.objects.filter(screenName=screen_name).exists():
				screenObj = screen.objects.filter(screenName=screen_name)[0]
				if not seat.objects.filter(screenId=screenObj.screenId, rowName=rowChoice, seatNo =  seatNo,status=1).exists():
					totalSeats = len(seat.objects.filter(screenId=screenObj.screenId, rowName=rowChoice))
					unreservedCount = len(seat.objects.filter(screenId=screenObj.screenId, rowName=rowChoice, status=0))
					if unreservedCount < numSeats:
						return JsonResponse({'code':500,'message':'number of desired seats are greater than unreserved seats!'})
					else:
						seatsObj = seat.objects.filter(screenId=screenObj.screenId, rowName=rowChoice).order_by('seatNo')
						if seatsObj[seatNo].isAisle == 0:
							res = giveOptimiziedSeats(seatsObj, numSeats, seatNo, [seatNo], 0 , 0)
							if res == -1:
								return JsonResponse({'code':500,'message':'desired allocation of seats not possible!'})
							else:
								res.sort()
								return JsonResponse({'availableSeats':{str(rowChoice):res}})
						else:
							if (seatNo + 1)!= len(seatsObj):
								if seatsObj[seatNo + 1].isAisle != 1 and seatsObj[seatNo + 1].status==0:
									res = giveOptimiziedSeats(seatsObj, numSeats, seatNo, [seatNo], -1, 0)
									if res == -1:
										return JsonResponse({'code':500,'message':'desired allocation of seats not possible!'})
									else:
										res.sort()
										return JsonResponse({'availableSeats':{str(rowChoice):res}})
							if (seatNo-1) >= 0:
								if seatsObj[seatNo-1].isAisle != 1 and seatsObj[seatNo-1].status==0:
									res = giveOptimiziedSeats(seatsObj, numSeats, seatNo, [seatNo], 0, -1)
									if res == -1:
										return JsonResponse({'code':500,'message':'desired allocation of seats not possible!'})
									else:
										res.sort()
										return JsonResponse({'availableSeats':{str(rowChoice):res}})
							return JsonResponse({'code':500,'message':'desired allocation of seats not possible!'})
				else:
					return JsonResponse({'code':500,'message':'seat '+choice+' already booked'})
			else:
				return JsonResponse({'code':500,'message':'Screen does not exist'})
		else:
			return JsonResponse({'code':500,'message':'data incorrect'})
	except Exception as e:
		return JsonResponse({'code':500,'message':'Some problem has occured.'})


def giveOptimiziedSeats(obj, numSeats, index, list1, flag1, flag2):
	i = index-1
	j = index+1
	flag1 = 0
	flag2 = 0
	while flag1 != -1 or flag2 != -1:
		if flag1 != -1 and i >= 0:		
			if obj[i].status == 0:
				if obj[i].isAisle == 0:
					list1.append(obj[i].seatNo)
					if len(list1) == numSeats:
						return list1
				else:
					list1.append(obj[i].seatNo)
					flag1 = -1
					if len(list1) == numSeats:
						return list1
			else:
				flag1 = -1

		if flag2 != -1 and j < len(obj):
			if obj[j].status == 0:	
				if obj[j].isAisle == 0:
					list1.append(obj[j].seatNo)
					if len(list1) == numSeats:
						return list1
				else:
					list1.append(obj[j].seatNo)
					flag2 = -1
					if len(list1) == numSeats:
						return list1
			else:
				flag2 = -1

		i = i - 1
		j = j + 1
		

	if len(list1) != numSeats:
		return (-1)














