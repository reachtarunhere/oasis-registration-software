from registration.models import *
from models import *
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
import string
from random import randint
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.
def encode_glid(gl_id):
	gl_ida = '0'*(4-len(str(gl_id)))+str(gl_id)
	mixed = string.ascii_uppercase + string.ascii_lowercase
	count = 51
	encoded = ''
	for x in gl_ida:
		encoded = encoded + x
		encoded = encoded + mixed[randint(0,51)]
	return encoded
def get_barcode(request):
	list_of_people_selected = InitialRegistration.objects.all()
	list_of_people_selected = [x for x in list_of_people_selected if x.user]
	final_display = []
	for x in list_of_people_selected:
		gl_id = x.id
		name = x.name
		college = x.college
		encoded = encode_glid(gl_id)
		final_display.append((name,college,encoded))
	context = RequestContext(request)
	context_dict = {'final_display':final_display}
	return render_to_response('get_barcode.html', context_dict, context)

def showteam(request,gl_id): #shows team members who have checked in from firewallz booth for teams
	gl = InitialRegistration.objects.get(id=gl_id)
	participant_list = gl.user.participant_set.all()
	final = [x for x in participant_list if x.firewallz==True]
	context = RequestContext(request)
	context_dict = {'final':final}
	return render_to_response('teamdetails.html', context_dict, context)
####################################Firewallz outer booth code#######################################
#####################################################################################################

def firewallzo_gl(request): #team details editable on first view
	#add gl_name to context dict
	if request.POST:
		if str(request.POST['formtype']) == 'finalform':
			list_of_people_selected = request.POST.getlist('left')
			selectedpeople_list = [int(x) for x in list_of_people_selected]
			display_table = []
			for x in selectedpeople_list:
				participant = Participant.objects.get(id=x)
				participant.firewallz = True
				participant.save()
				participant_name = str(participant.name)
				participant_gender = str(participant.gender)[0].upper()
				if len(participant.events.all()): #checks if the participant has the event otherwise the lenth of the list will be zero
						participant_event_list = [x.name for x in participant.events.all()]
						participant_event = ','.join(participant_event_list)
				else:
					participant_event = ''
				display_table.append((participant_name,participant_gender,participant_event))
			context = RequestContext(request)
			context_dict = {'display_table':display_table}
			return render_to_response('firewallzo_checkout.html', context_dict, context)

		try:
			encoded=request.POST['code']
			decoded = encoded[0]+encoded[2]+encoded[4]+encoded[6] #taking alternative character because alphabets were random and had no meaning
			gl_id = int(decoded) #to remove preceding zeroes and get user profile
			gl = InitialRegistration.objects.get(id=gl_id)
		except:
			error="Invalid code entered " +encoded
			context = RequestContext(request)
			context_dict = {'error':error}
			return render_to_response('firewallzo_home.html', context_dict, context)

		participant_list = gl.user.participant_set.all() 
		college = str(gl.college)
		gl_name = str(gl.name)
		display_participants = []
		done_participants = []
		for p in participant_list:
			participant_name = str(p.name) 
			participant_gender = str(p.gender)[0].upper()#for using just M or F instead of fulll to save space.
			participant_id = int(p.id)
			if len(p.events.all()): #checks if the participant has the event otherwise the lenth of the list will be zero
				participant_event_list = [x.name for x in p.events.all()]
				participant_event = ','.join(participant_event_list)
			else:
				participant_event = '' #done because faculty is not assigned any event
			if p.firewallz != True: #list only particiants whose case is not finalized
				display_participants.append((participant_name,participant_gender,participant_id,participant_event))
			else:
				done_participants.append((participant_name,participant_gender,participant_id,participant_event))

		context = RequestContext(request)
		context_dict = {'display_participants': display_participants, 'college':college, 'gl_name':gl_name,'done_participants':done_participants,'gl':gl}
		return render_to_response('firewallzo_gl.html', context_dict, context)
	else:
		context = RequestContext(request)
		error = ''
		context_dict = {'error':error}
		return render_to_response('firewallzo_home.html', context_dict, context)


@staff_member_required
def firewallzo_remove_people(request,gl_id):
	if request.POST:
		list_of_people_selected = request.POST.getlist('remove')
		selectedpeople_list = [int(x) for x in list_of_people_selected]
		removed_people = []
		for x in selectedpeople_list:
			participant = Participant.objects.get(id=x)
			participant.firewallz = False
			participant.save()
			participant_name = str(participant.name) 
			participant_gender = str(participant.gender[0].upper())
			if len(participant.events.all()): #checks if the participant has the event otherwise the lenth of the list will be zero
				participant_event_list = [x.name for x in participant.events.all()]
				participant_event = ','.join(participant_event_list)
			else:
				participant_event = ''
			removed_people.append((participant_name,participant_gender,participant_event))
		gl = InitialRegistration.objects.get(id=gl_id)
		participant_list = gl.user.participant_set.all()
		approved_participant_list = [x for x in participant_list if x.firewallz == True]
		encoded = encode_glid(gl_id)
		context = RequestContext(request)
		context_dict = {'removed_people':removed_people,'approved_participant_list':approved_participant_list, 'gl_id':gl_id, 'encoded':encoded}
		return render_to_response('firewallzo_remove.html', context_dict, context)
	else:
		gl = InitialRegistration.objects.get(id=gl_id)
		participant_list = gl.user.participant_set.all()
		approved_participant_list = [x for x in participant_list if x.firewallz == True]
		encoded = encode_glid(gl_id)		
		context = RequestContext(request)
		context_dict = {'approved_participant_list':approved_participant_list, 'gl_id':gl_id,'encoded':encoded}
		return render_to_response('firewallzo_remove.html', context_dict, context)


@staff_member_required
def firewallzo_add_participant(request,gl_id):
	event_list = EventNew.objects.all()
	c = Category.objects.get(name='other')
	category_list = [x for x in Category.objects.all() if x != c]
	category_event_list = []
	event_list = [x for x in event_list if x.category != category_list]
	category_name_list = [x.name for x in category_list]

	try:
		gl=InitialRegistration.objects.get(id=int(gl_id))
		message = ''
	except:
		return HttpResponse('try again')
	if request.POST:
		# try:
		# 	gl=InitialRegistration.objects.get(id=int(gl_id))
		# except:
		# 	return HttpResponse('Invalid Group Leader')
		participant_name=request.POST['name']
		participant_gender = request.POST['gender']
		participant_contact = request.POST['contact']
		participant_email = request.POST['email']
		par = request.POST.getlist('eventList')
		participant_event_list_final = [int(x) for x in par]
		participant_gl = gl.user
		participant_college = gl.college
		p = Participant(name=participant_name,phone=participant_contact,email_id=participant_email,gleader=gl.user,gender=participant_gender)
		p.save()
		#Now add events

		for event_id in participant_event_list_final:
			participant_event = EventNew.objects.get(id=event_id)
			p.events.add(participant_event)
		p.save()

		#save participant
		message="New Participant added successfully"

	encoded = encode_glid(gl_id)	
	context = RequestContext(request)
	context_dict = {'message':message, 'encoded':encoded,'gl_id':gl_id, 'event_list':event_list, 'category_name_list':category_name_list}
	return render_to_response('firewallzo_add.html', context_dict, context)
 #currently allows only change of name and gender on firewalzz booth
@staff_member_required
def firewallzo_edit_participant(request,participant_id):
	try:
		participant=Participant.objects.get(id=int(participant_id))
		message = ''
	except:
		return HttpResponse('try again')
	if request.POST:
		participant.name=request.POST['name']
		participant.gender = request.POST['gender']
		participant.save()
		message="Participant Details changed successfully"
	gl_id = int(participant.gleader.initialregistration_set.all()[0].id)
	encoded = encode_glid(gl_id)
	context = RequestContext(request)
	context_dict = {'participant':participant,'message':message, 'encoded':encoded,'gl_id':gl_id}

	return render_to_response('firewallzo_edit.html', context_dict, context)


@staff_member_required
def firewallzo_checkout(request):
	selectedpeople = request.session.get('selectedpeople')
	selectedpeople_list = selectedpeople.split()
	selectedpeople_list = [int(x) for x in selectedpeople_list]
	display_table = []
	for x in selectedpeople_list:
		participant = Participant.objects.get(id=x)
		participant.firewallz = True
		participant.save()
		participant_name = str(participant.name) 
		participant_gender = str(participant.gender)[0].upper()
		if len(participant.events.all()): #checks if the participant has the event otherwise the lenth of the list will be zero
				participant_event = str(participant.events.all()[0].name)
		display_table.append((participant_name,participant_gender,participant_event))
	context = RequestContext(request)
	context_dict = {'display_table':display_table}
	return render_to_response('firewallzo_checkout.html', context_dict, context)


@staff_member_required
def firewallzo_gl_reassign(request,gl_id):
	if request.POST:
		if str(request.POST['formtype']) == 'finalform':
			newglidlist = str(request.session.get('newglidlist')).split(' ')
			newglidlist = [int(x) for x in newglidlist]
			selected_participant_id=int(request.POST['newgl'])
			participant = Participant.objects.get(id= selected_participant_id)
			#creating user for participant
			final_member_list = [Participant.objects.get(id=x) for x in newglidlist]
			participant_username = str(participant.name).replace(' ','') + str(randint(100,9999))
			if participant.email_id:
				participant_email = participant.email_id
			else:
				participant_email = 'abc@abc.com'
			u = User(username=participant_username, email = participant_email)
			u.save()
			password = randint(1000,9999)
			u.set_password(password)
			#Creating InitialRegistration for participant
			participant_name = participant.name
			participant_college = participant.gleader.initialregistration_set.all()[0].college
			participant_gender = participant.gender
			participant_contact_no = participant.phone
			participant_city = participant.gleader.initialregistration_set.all()[0].city
			newgl = InitialRegistration(name=participant.name,user=u,college=participant_college,gender=participant.gender,phone=participant.phone,city =participant_city)
			newgl.save()
			#assigining the new gl to all selected people
			for x in newglidlist:
				part = Participant.objects.get(id=x)
				part.gleader = newgl.user
				part.save()
			#Generating uniquecode for new_gl
			new_gl_id = newgl.id
			gl_ida = '0'*(4-len(str(new_gl_id)))+str(new_gl_id)
			mixed = string.ascii_uppercase + string.ascii_lowercase
			count = 51
			new_encoded = ''
			for x in gl_ida:
				new_encoded = new_encoded + x
				new_encoded = new_encoded + mixed[randint(0,51)]
			#new_encoded is the unique id of the new_gl
			context = RequestContext(request)
			context_dict = {'newgl':newgl,'new_encoded':new_encoded,'password':password, 'participant_username':participant_username,'final_member_list':final_member_list}
			return render_to_response('newgl_checkout.html', context_dict, context)
		else:#radio button form
			try:
				new_members_id = request.POST.getlist('newglmember')
				new_members_id = [str(x) for x in new_members_id]
				new_members_id_string = ' '.join(new_members_id)
				new_members_id = [int(x) for x in new_members_id]
			except:
				orignal_gl = InitialRegistration.objects.get(id=gl_id).user
				participant_list = orignal_gl.participant_set.all()
				not_approved_paticipants = [x for x in participant_list if x.firewallz != True]
				error = 'No selection made'
				context = RequestContext(request)
				context_dict = {'not_approved_participants':not_approved_participants,'error':error,'gl_id':gl_id}
				return render_to_response('newglcheckbox.html', context_dict, context)
			
			request.session['newglidlist'] = new_members_id_string
			new_members_list = [Participant.objects.get(id=y) for y in new_members_id]
			context = RequestContext(request)
			context_dict = {'new_members_list':new_members_list,'gl_id':gl_id}
			return render_to_response('newglradio.html', context_dict, context)

	else:
		orignal_gl = InitialRegistration.objects.get(id=gl_id).user
		participant_list = orignal_gl.participant_set.all()
		not_approved_participants = [x for x in participant_list if x.firewallz != True]
		error = ''
		context = RequestContext(request)
		context_dict = {'not_approved_participants':not_approved_participants,'error':error,'gl_id':gl_id}
		return render_to_response('newglcheckbox.html', context_dict, context)



# 
# @staff_member_required
# def firewallz_fid(request):
# 	if request.POST:


# 		if str(request.POST['formtype']) == 'finalform':
# 			gl_id = int(request.session.get('glidfire'))
# 			gl = InitialRegistration.objects.get(id=gl_id)
# 			participant_list = gl.user.participant_set.all()
# 			firewallz_approved = [x for x in participant_list if x.firewallz == True and not bool(x.fireid)]
# 			for x in firewallz_approved:
# 				fid = request.POST['fid'+str(x.id)]
# 				x.fireid = fid
# 				x.save()
# 			done_list = [x for x in participant_list if x.firewallz == True and bool(x.fireid)]
# 			firewallz_approved = [x for x in participant_list if x.firewallz == True and not bool(x.fireid)]
# 			context = RequestContext(request)
# 			context_dict = {'firewallz_approved':firewallz_approved,'done_list':done_list}
# 			return render_to_response('firewallzi_checkout.html', context_dict, context)
# 		try:
# 			encoded=request.POST['code']
# 			decoded = encoded[0]+encoded[2]+encoded[4]+encoded[6] #taking alternative character because alphabets were random and had no meaning
# 			gl_id = int(decoded) #to remove preceding zeroes and get user profile
# 			gl = InitialRegistration.objects.get(id=gl_id)
# 			request.session['glidfire'] = str(gl_id)
# 		except:
# 			error="Invalid code entered " +encoded
# 			context = RequestContext(request)
# 			context_dict = {'encoded':encoded}
# 			return render_to_response('firewallzi_home.html', context_dict, context)
# 		else:
# 			gl_id = int(request.session.get('glidfire'))
# 			gl = InitialRegistration.objects.get(id=gl_id)
# 			participant_list = gl.user.participant_set.all()
# 			firewallz_approved = [x for x in participant_list if x.firewallz == True and not bool(x.fireid)]
# 			done_list = [x for x in participant_list if x.firewallz == True and bool(x.fireid)]
# 			context = RequestContext(request)
# 			context_dict = {'firewallz_approved':firewallz_approved,'done_list':done_list}
# 			return render_to_response('firewallzi_checkout.html', context_dict, context)
# 	else:
# 		context = RequestContext(request)
# 		error = ''
# 		context_dict = {'error':error}
# 		return render_to_response('firewallzi_home.html', context_dict, context)


def reconec_home(request):
	#simple template to enter id
	if request.POST:


		try:
			encoded=request.POST['code']
			decoded = encoded[0]+encoded[2]+encoded[4]+encoded[6] #taking alternative character because alphabets were random and had no meaning
			gl_id = int(decoded) #to remove preceding zeroes and get user profile
			gl = InitialRegistration.objects.get(id=gl_id)
		except:
			error="Invalid code entered " +encoded
			context = RequestContext(request)
			context_dict = {'error':error}
			return render_to_response('reconec_home2.html', context_dict, context)

		participant_list = gl.user.participant_set.all() 
		college = str(gl.college)
		gl_name = str(gl.name)
		display_participants = []
		done_participants = []
		no_males=0
		no_females=0
		for p in participant_list:
			if p.gender[0].upper()=="M" and p.firewallz ==True and p.acco!=True:
				no_males+=1
			elif p.gender[0].upper()=="F" and p.firewallz ==True and p.acco!=True:
				no_females+=1		
			participant_name = str(p.name) 
			participant_gender = str(p.gender)[0].upper()#for using just M or F instead of fulll to save space.
			participant_id = int(p.id)
			if p.acco == True and p.room:
				participant_room = str(p.room.room)+' '+p.room.bhavan.name
			else:
				participant_room = ''
			# if len(p.events.all()): #checks if the participant has the event otherwise the lenth of the list will be zero
			# 	participant_event = str(p.events.all()[0].name)
			# else:
			# 	participant_event = '' #done because faculty is not assigned any event
			if p.firewallz == True: #list only particiants who have been approved by firewallz
				display_participants.append((participant_name,participant_gender,participant_id,participant_room))
		done_participants = [x for x in participant_list if x.firewallz==True and x.acco==True]
		context = RequestContext(request)
		context_dict = {'done_participants':done_participants,'display_participants': display_participants, 'college':college, 'no_males':no_males, 'no_females':no_females,
		'gl_name':gl_name,'done_participants':done_participants, "gl_id":gl_id}
		return render_to_response('reconec_gl.html', context_dict, context)
	else:
		context = RequestContext(request)
		error = ''
		context_dict = {'error':error}
		return render_to_response('reconec_home2.html', context_dict, context)


@staff_member_required
def acco_list(request,gl_id):

	#list acco with availibilty
	#ability to select
	bhavan_list= Bhavan.objects.all()
	initial_vacancy_display= []
	vacancy_display = []
	for bhavan in bhavan_list:
		if bhavan.id != 1:
			bhavan_name = bhavan.name
			rooms = bhavan.room_set.all()
			initial_vacancy_display.append((bhavan_name,rooms))
	all_rooms = []
	for bhavan in bhavan_list:
		if bhavan.id != 1:
			bhavan_name = bhavan.name
			rooms = [x for x in bhavan.room_set.all() if x.vacancy != 0]
			all_rooms += rooms
			if len(rooms):
				vacancy_display.append((bhavan_name,rooms))
	gl = InitialRegistration.objects.get(id=gl_id)
	participant_list = gl.user.participant_set.all() 
	no_males=0
	no_females=0
	for p in participant_list:
		if p.gender[0].upper()=="M" and p.firewallz ==True and p.acco!=True:
			no_males+=1
		elif p.gender[0].upper()=="F" and p.firewallz ==True and p.acco!=True:
			no_females+=1
	if request.POST:
	
		try:
			roomid=request.POST['roomid']
			x = roomid + 'alloted'
			noalloted=int(request.POST[x])
			roomid = int(roomid)
		except:
			error="Invalid Room Selected"
			context = RequestContext(request)
			context_dict = {'error':error}
			return render_to_response('reconec_acco.html', context_dict, context)
		selectedroom = Room.objects.get(id=roomid)
		selectedroom_availibilty = selectedroom.vacancy
		unalloted_males = [x for x in participant_list if x.firewallz == True and x.gender[0].upper() == 'M' and x.acco != True]
		unalloted_females = [x for x in participant_list if x.firewallz == True and x.gender[0].upper() == 'F' and x.acco != True]
		if selectedroom.bhavan.name == 'MB' or selectedroom.bhavan.name == 'MB 1' or selectedroom.bhavan.name == 'MB 3' or selectedroom.bhavan.name == 'MB 4' or selectedroom.bhavan.name == 'MB 5' or selectedroom.bhavan.name == 'MB 6-1' or selectedroom.bhavan.name == 'MB 6-2'or selectedroom.bhavan.name == 'MB 9' or selectedroom.bhavan.name == 'SQ' or selectedroom.bhavan.name == 'CVR': #use or for extra bhavanas
			if no_females<noalloted:
				return HttpResponse('error: No of rooms is not corresponding with entries.')
			for y in range(noalloted):
				unalloted_females[y].acco=True
				unalloted_females[y].room = selectedroom
				selectedroom.vacancy -= 1
				selectedroom.save()
				unalloted_females[y].save()
		
		else:
			if no_males<noalloted:
				return HttpResponse('error: No of rooms is not corresponding with entries.')
			for y in range(noalloted):
				unalloted_males[y].acco=True
				unalloted_males[y].room = selectedroom
				selectedroom.vacancy -= 1
				selectedroom.save()
				unalloted_males[y].save()
		#return HttpResponse(selectedroom.vacancy)
		no_males=0
		no_females=0
		participant_list = gl.user.participant_set.all()
		for p in participant_list:
			if p.gender[0].upper()=="M" and p.firewallz ==True and p.acco!=True:
				no_males+=1
			elif p.gender[0].upper()=="F" and p.firewallz ==True and p.acco!=True:
				no_females+=1
		bhavan_list= Bhavan.objects.all()
		all_rooms =[]
		for bhavan in bhavan_list:
			if bhavan.id != 1:
				bhavan_name = bhavan.name
				rooms = [x for x in bhavan.room_set.all() if x.vacancy != 0]
				all_rooms += rooms
				if len(rooms):
					vacancy_display.append((bhavan_name,rooms))
		done_participants = [x for x in participant_list if x.firewallz==True and x.acco==True]
		context = RequestContext(request)
		context_dict = {'done_participants':done_participants,'all_rooms':all_rooms,'no_males':no_males, 'no_females':no_females,"gl_id":gl_id, 'vacancy_display':vacancy_display}
		return render_to_response('reconec_acco.html', context_dict, context)

	else:
		done_participants = [x for x in participant_list if x.firewallz==True and x.acco==True]
		context = RequestContext(request)
		context_dict = {'done_participants':done_participants,'all_rooms':all_rooms,'vacancy_display':vacancy_display, 'no_males':no_males, 'no_females':no_females, "gl_id":gl_id}
		return render_to_response('reconec_acco.html', context_dict, context)
@staff_member_required
def all_bhawans(request):
	bhavan_list= Bhavan.objects.all()
	all_rooms = []
	for bhavan in bhavan_list:
		bhavan_name = bhavan.name
		rooms = [x for x in bhavan.room_set.all()]
		all_rooms += rooms
	context = RequestContext(request)
	context_dict = {'all_rooms':all_rooms}
	return render_to_response('all_bhavans.html', context_dict, context)


@staff_member_required
def room_details(request):
	room_list= [x for x in Room.objects.all() if x.id != 1]
	room_list_mod = [(str(x.bhavan.name)+' '+str(x.room)+'#'+str(x.id),x) for x in room_list]
	if request.POST:
		roomid=str(request.POST['roomid'])
		roomid = int(roomid[roomid.find('#')+1:])
		selectedroom = Room.objects.get(id=roomid)
		room_participants = selectedroom.participant_set.all()
		gl_list = []
		gl_count = {}
		for p in room_participants:
			if p.gleader.initialregistration_set.all()[0] not in gl_list:
				gl_list.append(p.gleader.initialregistration_set.all()[0])
				gl_count[p.gleader.initialregistration_set.all()[0]] = 1
			else:
				gl_count[p.gleader.initialregistration_set.all()[0]] += 1

		context = RequestContext(request)
		context_dict = {'gl_list':gl_list, 'room_list_mod':room_list_mod, 'gl_count':gl_count}
		return render_to_response('room_details.html', context_dict, context)

	context = RequestContext(request)
	context_dict = {'room_list_mod':room_list_mod}
	return render_to_response('room_details.html', context_dict, context)	


@staff_member_required
def reconec_deallocate(request,gl_id):
	gl = InitialRegistration.objects.get(id=gl_id)
	alloted_people = [x for x in gl.user.participant_set.all() if x.firewallz == True and x.acco == True]
	if request.POST:
		try:
			list_of_people_selected = request.POST.getlist('deallocate')
		except:
			return HttpResponse('No one was selected')
		selected_people_list = [int(x) for x in list_of_people_selected]
		done_people = []
		for x in selected_people_list:
			p= Participant.objects.get(id=x)
			p.acco = False
			selected_room = p.room
			selected_room.vacancy += 1
			selected_room.save()
			p.room = None
			p.save()
			done_people.append(p)
		alloted_people = [x for x in gl.user.participant_set.all() if x.firewallz == True and x.acco == True]
		context = RequestContext(request)
		context_dict = {'done_people':done_people, 'alloted_people':alloted_people,"gl_id":gl_id}
		return render_to_response('reconec_deallocate.html', context_dict, context)
	else:
		done_people = []
		context = RequestContext(request)
		context_dict = {'done_people':done_people, 'alloted_people':alloted_people,"gl_id":gl_id}
		return render_to_response('reconec_deallocate.html', context_dict, context)
		

@staff_member_required
def phonedetails(request,gl_id):
	gl = InitialRegistration.objects.get(id=gl_id)
	participant_list = gl.user.participant_set.all()
	context = RequestContext(request)
	context_dict = {'participant_list':participant_list}
	return render_to_response('reconec_phone.html', context_dict, context)



@staff_member_required
def reconec_checkout(request,gl_id):
	#simple template to enter id
	postcheck = False
	if request.POST:
		postcheck = True
		try:
			list_of_people_selected = request.POST.getlist('checkout')
		except:
			return HttpResponse('error')

		selectedpeople_list = [int(x) for x in list_of_people_selected]
		display_table = []
		for x in selectedpeople_list:
			participant = Participant.objects.get(id=x)
			participant_room = participant.room
			participant_room.vacancy += 1
			participant_room.save()
			participant.room = Room.objects.get(id=1)
			croom = Room.objects.get(id=1)
			croom.vacancy -= 1
			croom.save()
			participant.save()
			participant_name = str(participant.name) 
			participant_gender = str(participant.gender)[0].upper()
			if len(participant.events.all()): #checks if the participant has the event otherwise the lenth of the list will be zero
					participant_event = str(participant.events.all()[0].name)
			else:
				participant_event = ''
			display_table.append((participant_name,participant_gender,participant_event))
		gl = InitialRegistration.objects.get(id=gl_id)
		participant_list = gl.user.participant_set.all() 
		college = str(gl.college)
		gl_name = str(gl.name)
		final_participants = [x for x in participant_list if x.firewallz==True and x.acco==True and x.room.bhavan.id != 1]
		context = RequestContext(request)
		context_dict = {'final_participants':final_participants,'college':college,"gl_id":gl_id,'display_table':display_table}
		return render_to_response('reconec_checkout.html', context_dict, context)


	else:
		gl = InitialRegistration.objects.get(id=gl_id)
		participant_list = gl.user.participant_set.all() 
		college = str(gl.college)
		gl_name = str(gl.name)
		final_participants = [x for x in participant_list if x.firewallz==True and x.acco==True and x.room.bhavan.id != 1]
		context = RequestContext(request)
		context_dict = {'final_participants':final_participants, 'college':college,"gl_id":gl_id}
		return render_to_response('reconec_checkout.html', context_dict, context)
@staff_member_required
def college_in_bhavan(request):
	colleges = {}
	bhavan_list = Bhavan.objects.all()

	for bhavan in bhavan_list:
		colleges[bhavan.name] = []
		for room in bhavan.room_set.all():
			for participant in room.participant_set.all():
				participant_college = participant.gleader.initialregistration_set.all()[0].college
				if participant_college not in colleges[bhavan.name]:
					colleges[bhavan.name].append(participant_college)
	display = []
	for x in colleges:
		for y in colleges[x]:
			display.append((x,y))

	context = RequestContext(request)
	context_dict = {'display':display}
	return render_to_response('reconec_bhavanwise.html', context_dict, context)


def receipt(request):
	if request.POST:


		try:
			encoded=request.POST['code']
			decoded = encoded[0]+encoded[2]+encoded[4]+encoded[6] #taking alternative character because alphabets were random and had no meaning
			gl_id = int(decoded) #to remove preceding zeroes and get user profile
			gl = InitialRegistration.objects.get(id=gl_id)
		except:
			error="Invalid code entered " +encoded
			context = RequestContext(request)
			context_dict = {'error':error}
			return render_to_response('controlzhome.html', context_dict, context)
		college = gl.college
		uid = encoded
		people = [x for x in gl.user.participant_set.all() if x.firewallz == True and x.controlzpay != True]
		done_participants = [x for x in gl.user.participant_set.all() if x.firewallz == True and x.controlzpay == True]
		request.session['uid'] = encoded
		# count=0
		# for ppl in people:
		# 	if ppl.controlzpay == True:
		# 		count+=1
		error = ''
		if len(people)==0:
			error="No receipt can be generated now."
			context = RequestContext(request)
			context_dict = {'error':error}
			return render_to_response('controlzhome.html', context_dict, context)

		context = RequestContext(request)
		context_dict = {'people':people, 'done_participants':done_participants,'gl_id':gl.id,'encoded':encoded}
		return render_to_response('controlgl.html', context_dict, context)		


	else:
		return render_to_response('controlzhome.html')


def generate_receipt(request,gl_id):
	gl = InitialRegistration.objects.get(id=gl_id)
	people = [x for x in gl.user.participant_set.all() if x.firewallz == True and x.controlzpay != True and x.coach != True]
	for part in people:
		part.controlzpay= True
		part.save()
	number_of_participants = len(people)
	register=750
	#calculationg amount
	amount=750*number_of_participants
	#now make bill
	bill_no_raw = len(bill.objects.all()) + 1
	a = bill()
	a.gleader = gl.name
	a.college = gl.college
	a.number = bill_no_raw 
	a.amount = amount
	a.save()
	rec = '0'*(4-len(str(bill_no_raw)))+str(bill_no_raw)
	uid = request.session['uid']
	return render_to_response('receipt.html',{'college':gl.college,'uid':uid,'register':register,'amount':amount,'receiptno':rec})

def controlz_edit_participant(request,participant_id):
	try:
		participant=Participant.objects.get(id=int(participant_id))
		message = ''
	except:
		return HttpResponse('try again')
	#participant_selected_events = [event for event in participant.events.all()]
	p = participant
	event_list = EventNew.objects.all()
	c = Category.objects.get(name='other')
	category_list = [x for x in Category.objects.all() if x != c]
	category_event_list = []
	event_list = [x for x in event_list if x.category != c]
	category_name_list = [x.name for x in category_list]
	participant_event_list = participant.events.all()
	event_add_list = [x for x in event_list if x not in participant_event_list]

	if request.POST:
		try:
			addorremove = request.POST['addorremove']
		except:
			return HttpResponse('error')
		if addorremove == 'add':
			selected_event_name = request.POST['eventselected']
			selected_event = EventNew.objects.get(name=selected_event_name)
			p.events.add(selected_event)
			p.save()
			message="Participant Details changed successfully"
		elif addorremove == 'remove':
			selected_event_name = request.POST['eventselected']
			selected_event = EventNew.objects.get(name=selected_event_name)
			p.events.remove(selected_event)
			p.save()
			message="Participant Details changed successfully"
	participant_event_list = participant.events.all()
	event_add_list = [x for x in event_list if x not in participant_event_list]
	gl_id = int(participant.gleader.initialregistration_set.all()[0].id)
	encoded = encode_glid(gl_id)
	context = RequestContext(request)
	context_dict = {'event_add_list':event_add_list,'category_name_list':category_name_list,'participant':participant,'message':message, 'encoded':encoded,'gl_id':gl_id,'event_list':event_list,'participant_event_list':participant_event_list}

	return render_to_response('controlz_edit.html', context_dict, context)


@staff_member_required
def controlz_event_details(request):
	c = Category.objects.get(name='other')
	event_list= [x for x in EventNew.objects.all() if x.category != c]
	event_list_mod = [(str(x.name)+'#'+str(x.id),x) for x in event_list]
	if request.POST:
		eventid=str(request.POST['eventid'])
		eventid = int(eventid[eventid.find('#')+1:])
		selected_event = EventNew.objects.get(id=eventid)
		event_participants_temp = [x for x in selected_event.participant_set.all() if x.controlzpay == True]
		event_participants = [(x,x.gleader.initialregistration_set.all()[0].college) for x in selected_event.participant_set.all() if x.controlzpay == True]
		no_males = len([x for x in event_participants_temp if x.gender[0].upper() == 'M'])
		no_females = len(event_participants)-no_males
		context = RequestContext(request)
		context_dict = {'event_participants':event_participants, 'event_list_mod':event_list_mod,'no_males':no_males,'no_females':no_females}
		return render_to_response('controlz_event_details.html', context_dict, context)

	context = RequestContext(request)
	context_dict = {'event_list_mod':event_list_mod}
	return render_to_response('controlz_event_details.html', context_dict, context)	