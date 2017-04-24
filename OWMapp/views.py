from django.shortcuts import render
import requests
import json
import pyowm 
# from yelpapi import YelpAPI
from googleplaces import GooglePlaces, types, lang
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

import sqlite3

# Create your views here.
# reference: http://drksephy.github.io/2015/07/16/django/

#For future reference, tweak database to account for date 


def home(request):
    return render(request, 'home.html')
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def activities(request):
    parsedData = []
    
    owm = pyowm.OWM('c646db9215792630a0891c27e40c6745')
    google_places = GooglePlaces('AIzaSyC_fBaJydXEGKLLqq5Ym2lCXZ9glOvPqFg') 
    
    if request.method == 'POST':
        
        city = request.POST.get('search-term')
        
        activitiesData = {}  
                
        forecast = owm.weather_at_place(city)
        w = forecast.get_weather()
        status = w.get_status()
        humidity = w.get_humidity()  
        temperature = w.get_temperature()
        wind = w.get_wind()

        temp = int(round((((temperature['temp'] - 273.15) * 9 / 5) + 32), 0))
        wind_speed = wind['speed']
        
        if (status == "Rain" or status == "Snow" or temp < 32):
            query_result = google_places.nearby_search(
            location=city, keyword='',
            radius=20000, types=[types.TYPE_AQUARIUM, types.TYPE_ART_GALLERY, types.TYPE_BOWLING_ALLEY, types.TYPE_MUSEUM,
                                 types.TYPE_MOVIE_THEATER, types.TYPE_SHOPPING_MALL])
            
        elif (status == "Clear" or temp > 50):
            query_result = google_places.nearby_search(
            location=city, keyword='',
            radius=20000, types=[types.TYPE_AMUSEMENT_PARK, types.TYPE_CAMPGROUND, types.TYPE_ZOO,
                                 types.TYPE_PARK, types.TYPE_BICYCLE_STORE])
            
        
        else:  
            if (status == "Wind" or status == "Mist" or wind_speed > 15 or humidity > 80 and 32 < temp < 50):
                query_result = google_places.nearby_search(
                location=city, keyword='',
                types=[types.TYPE_AQUARIUM, types.TYPE_ART_GALLERY, types.TYPE_BOWLING_ALLEY, types.TYPE_MUSEUM,
                       types.TYPE_MOVIE_THEATER, types.TYPE_SHOPPING_MALL])
                                 
                
            else:
                query_result = google_places.nearby_search(
                location=city, keyword='',
                radius=20000, types=[types.TYPE_AMUSEMENT_PARK, types.TYPE_CAMPGROUND, types.TYPE_ZOO,
                                     types.TYPE_PARK, types.TYPE_BICYCLE_STORE])
                
                
        i = 0
        for place in query_result.places:
            activitiesData[i] = place.name
            i = i+1
            #print(place.name)
        
        parsedData.append(activitiesData)
        
    return render(request, 'activities.html', {'data': parsedData})

def weather(request):
    #template = loader.get_template('templates_app\weather.html')
    
    
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    #cur.execute('DROP TABLE IF EXISTS Weather ')

    cur.execute('CREATE TABLE IF NOT EXISTS Weather (city TEXT, status TEXT, humidity INTEGER, temperature INTEGER, wind INTEGER)')
    
#    print('Weather:')
#    cur.execute('SELECT city FROM Weather')
#    for row in cur :
#        print(row)
        
    conn.close()
    
    parsedData = []
    
    owm = pyowm.OWM('c646db9215792630a0891c27e40c6745')

    
    if request.method == 'POST':
        
        city = request.POST.get('search-term')
        
        cityData = {}  

        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM Weather WHERE city = '%s'" %city)
        x = cur.fetchone()  
        
        if (x != None):
            #print("Cached")            
            
            cityData['status'] = x[1]
            cityData['humidity'] = x[2]
            cityData['temperature'] = x[3]
            cityData['wind_speed'] = x[4]
            parsedData.append(cityData)
            
            cur.close()
            return render(request, 'weather.html', {'data': parsedData})

        cur.close()
                
        forecast = owm.weather_at_place(city)
        w = forecast.get_weather()
        status = w.get_status()
        humidity = w.get_humidity()  
        temperature = w.get_temperature()
        wind = w.get_wind()

        temp = int(round((((temperature['temp'] - 273.15) * 9 / 5) + 32), 0))
        wind_speed = wind['speed']
        
        if (wind_speed > 20):
            wind = "It is windy outside."
        else:
            wind = "It is not windy outside."
        
        cityData['status'] = status
        cityData['humidity'] = humidity
        cityData['temperature'] = temp
        cityData['wind_speed'] = wind
        
        parsedData.append(cityData)
        
        #print(parsedData)
        
        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        cur.execute('INSERT INTO Weather (city, status, humidity, temperature, wind) VALUES ( ?, ?, ?, ?, ? )', 
                (city, cityData['status'], cityData['humidity'], cityData['temperature'], cityData['wind_speed']))
        conn.commit()

        cur.close()
        
    return render(request, 'weather.html', {'data': parsedData})
    