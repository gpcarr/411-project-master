# -*- coding: utf-8 -*-
"""
Created on Thu Apr 27 10:23:30 2017

@author: Allison Kaufman
"""

from django.shortcuts import render
import requests
import json
import pyowm
import time
from yelpapi import YelpAPI
from googleplaces import GooglePlaces, types, lang
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

import sqlite3


# Create your views here.
# reference: http://drksephy.github.io/2015/07/16/django/

# For future reference, tweak database to account for date


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
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS Urls ')

    cur.execute(
        'CREATE TABLE IF NOT EXISTS Weather (city TEXT, status TEXT, humidity INTEGER, temperature INTEGER, wind INTEGER, date TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS Urls (place TEXT, url TEXT)')

    #    print('Weather:')
    #    cur.execute('SELECT city FROM Weather')
    #    for row in cur :
    #        print(row)

    conn.close()

    parsedData = []

    owm = pyowm.OWM('c646db9215792630a0891c27e40c6745')
    google_places = GooglePlaces('AIzaSyC_fBaJydXEGKLLqq5Ym2lCXZ9glOvPqFg')
    yelp_api = YelpAPI('sPHxGHzryB7B6BnzSjKwAA',
                       'YPgG1FcFFzDga6Pyxbl75oOKAjXusmMzpimp7DCpG6nTC25LcmvdPqVnBZHEeQxW')

    if request.method == 'POST':

        city = request.POST.get('search-term')

        activitiesData = {}

        date = time.strftime("%d/%m/%Y")

        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        cur.execute("SELECT * FROM Weather WHERE city = '%s'" % city)
        x = cur.fetchone()

        if (x != None):
            if (date == x[5]):

                status = x[1]
                humidity = x[2]
                temp = x[3]
                wind_speed = x[4]

                cur.close()

                if (status == "Rain" or status == "Snow" or temp < 32):
                    query_result = google_places.nearby_search(
                        location=city, keyword='',
                        radius=20000,
                        types=[types.TYPE_AQUARIUM, types.TYPE_ART_GALLERY, types.TYPE_BOWLING_ALLEY, types.TYPE_MUSEUM,
                               types.TYPE_MOVIE_THEATER, types.TYPE_SHOPPING_MALL])

                elif (status == "Clear" or temp > 50):
                    query_result = google_places.nearby_search(
                        location=city, keyword='',
                        radius=20000, types=[types.TYPE_AMUSEMENT_PARK, types.TYPE_CAMPGROUND, types.TYPE_ZOO,
                                             types.TYPE_PARK, types.TYPE_BICYCLE_STORE])


                else:
                    if (
                                    status == "Wind" or status == "Mist" or wind_speed == "It is windy outside." or humidity > 80 and 32 < temp < 50):
                        query_result = google_places.nearby_search(
                            location=city, keyword='',
                            types=[types.TYPE_AQUARIUM, types.TYPE_ART_GALLERY, types.TYPE_BOWLING_ALLEY,
                                   types.TYPE_MUSEUM,
                                   types.TYPE_MOVIE_THEATER, types.TYPE_SHOPPING_MALL])


                    else:
                        query_result = google_places.nearby_search(
                            location=city, keyword='',
                            radius=20000, types=[types.TYPE_AMUSEMENT_PARK, types.TYPE_CAMPGROUND, types.TYPE_ZOO,
                                                 types.TYPE_PARK, types.TYPE_BICYCLE_STORE])

                i = 0
                for place in query_result.places:

                    conn = sqlite3.connect('db.sqlite3')
                    cur = conn.cursor()

                    c = (place.name,)

                    cur.execute("SELECT * FROM Urls WHERE place =?", c)
                    x = cur.fetchone()

                    if (x != None):
                        print("Got the place: ", x[0], x[1])
                        activitiesData[i] = x[0]
                        i = i + 1
                        activitiesData[i] = x[1]
                        i = i + 1

                    else:

                        response = yelp_api.search_query(term=place.name, location=city, sort_by='rating', limit=1)

                        for key in response["businesses"]:
                            for key, values in key.items():
                                if (key == "url"):
                                    url = values

                        activitiesData[i] = place.name
                        i = i + 1
                        activitiesData[i] = url
                        i = i + 1

                        conn = sqlite3.connect('db.sqlite3')
                        cur = conn.cursor()

                        cur.execute('INSERT INTO Urls (place, url) VALUES ( ?, ? )',
                                    (place.name, url))
                        conn.commit()

                        cur.close()

                parsedData.append(activitiesData)
                cur.close()

            return render(request, 'activities.html', {'data': parsedData})

        forecast = owm.weather_at_place(city)
        w = forecast.get_weather()
        status = w.get_status()
        humidity = w.get_humidity()
        temperature = w.get_temperature()
        wind = w.get_wind()

        date_received = w.get_reference_time(timeformat='iso')
        date_received = str(date_received).split("-")

        month = date_received[1]
        year = date_received[0]
        day = date_received[2]
        day = day.split(" ")
        day = day[0]

        date_received = day + "/" + month + "/" + year

        temp = int(round((((temperature['temp'] - 273.15) * 9 / 5) + 32), 0))
        wind_speed = wind['speed']

        if (wind_speed > 20):
            wind = "It is windy outside."
        else:
            wind = "It is not windy outside."

        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        cur.execute('INSERT INTO Weather (city, status, humidity, temperature, wind, date) VALUES ( ?, ?, ?, ?, ?, ? )',
                    (city, status, humidity, temp, wind, date_received))
        conn.commit()

        cur.close()

        if (status == "Rain" or status == "Snow" or temp < 32):
            query_result = google_places.nearby_search(
                location=city, keyword='',
                radius=20000,
                types=[types.TYPE_AQUARIUM, types.TYPE_ART_GALLERY, types.TYPE_BOWLING_ALLEY, types.TYPE_MUSEUM,
                       types.TYPE_MOVIE_THEATER, types.TYPE_SHOPPING_MALL])

        elif (status == "Clear" or temp > 50):
            query_result = google_places.nearby_search(
                location=city, keyword='',
                radius=20000, types=[types.TYPE_AMUSEMENT_PARK, types.TYPE_CAMPGROUND, types.TYPE_ZOO,
                                     types.TYPE_PARK, types.TYPE_BICYCLE_STORE])


        else:
            if (
                                status == "Wind" or status == "Mist" or status == "Fog" or wind_speed > 15 or humidity > 80 and 32 < temp < 50):
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

            conn = sqlite3.connect('db.sqlite3')
            cur = conn.cursor()

            c = (place.name,)

            cur.execute("SELECT * FROM Urls WHERE place =?", c)
            x = cur.fetchone()

            if (x != None):

                activitiesData[i] = x[0]
                i = i + 1
                activitiesData[i] = x[1]
                i = i + 1

            else:
                response = yelp_api.search_query(term=place.name, location=city, sort_by='rating', limit=1)

                for key in response["businesses"]:
                    for key, values in key.items():
                        if (key == "url"):
                            url = values

                activitiesData[i] = place.name
                i = i + 1
                activitiesData[i] = url
                i = i + 1

                conn = sqlite3.connect('db.sqlite3')
                cur = conn.cursor()

                cur.execute('INSERT INTO Urls (place, url) VALUES ( ?, ? )',
                            (place.name, url))
                conn.commit()
                cur.close()
                # print(place.name)

        parsedData.append(activitiesData)

    return render(request, 'activities.html', {'data': parsedData})


def weather(request):
    date = time.strftime("%d/%m/%Y")

    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    # cur.execute('DROP TABLE IF EXISTS Weather ')

    cur.execute(
        'CREATE TABLE IF NOT EXISTS Weather (city TEXT, status TEXT, humidity INTEGER, temperature INTEGER, wind TEXT, date TEXT)')

    print('Weather:')
    cur.execute('SELECT city FROM Weather')
    for row in cur:
        print(row)

    conn.close()

    parsedData = []

    owm = pyowm.OWM('c646db9215792630a0891c27e40c6745')

    if request.method == 'POST':

        city = request.POST.get('search-term')

        cityData = {}

        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        cur.execute("SELECT * FROM Weather WHERE city = '%s'" % city)
        x = cur.fetchone()

        if (x != None):
            if (date == x[5]):
                print("New date: " + date)
                print("Old date: " + x[5])

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
        date_received = w.get_reference_time(timeformat='iso')
        date_received = str(date_received).split("-")

        month = date_received[1]
        year = date_received[0]
        day = date_received[2]
        day = day.split(" ")
        day = day[0]

        date_received = day + "/" + month + "/" + year

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
        cityData['date_received'] = date_received

        parsedData.append(cityData)

        # print(parsedData)

        conn = sqlite3.connect('db.sqlite3')
        cur = conn.cursor()

        cur.execute('INSERT INTO Weather (city, status, humidity, temperature, wind, date) VALUES ( ?, ?, ?, ?, ?, ? )',
                    (city, cityData['status'], cityData['humidity'], cityData['temperature'], cityData['wind_speed'],
                     cityData['date_received']))
        conn.commit()

        cur.close()

    return render(request, 'weather.html', {'data': parsedData})
