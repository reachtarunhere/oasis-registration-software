from django.db import models

# Create your models here.
class Bhavan(models.Model):
	name=models.CharField(max_length=50)
	def __unicode__(self):
		return self.name
class Room(models.Model):
	bhavan=models.ForeignKey('Bhavan')
	room=models.CharField(max_length=50)
	vacancy=models.IntegerField()
	def __unicode__(self):
		return str(self.room)
class bill(models.Model):
	gleader=models.CharField(max_length=80)
	amount=models.IntegerField()
	college=models.CharField(max_length=100)
	number = models.IntegerField()
	def __unicode__(self):
		return str(self.number)
