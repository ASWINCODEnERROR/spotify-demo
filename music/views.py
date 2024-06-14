from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
import requests
from bs4 import BeautifulSoup as bs
import re
import logging


# Create your views here.
def top_artists():
    url = "https://api.deezer.com/chart"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to get data: {response.status_code}")
        return []

    response_data = response.json()

    artists_info = []
    print(artists_info)

    if 'artists' in response_data:
        for artist in response_data['artists']['data']:
            name = artist.get('name', 'No Name')
            avatar_url = artist.get('picture_medium', 'No URL')
            artist_id = artist.get('id', 'No ID')
            artists_info.append((name, avatar_url, artist_id))

    return artists_info

# Example usage
artists = top_artists()
for artist in artists:
    print(artist)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def top_tracks():
    url = "https://api.deezer.com/chart"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        logger.info(f"Response data: {data}")

        track_details = []

        if 'tracks' in data:
            shortened_data = data['tracks']['data'][:18]

            for track in shortened_data:
                track_id = track.get('id', 'No ID')
                track_name = track.get('title', 'No Name')
                artist_name = track['artist'].get('name', 'No Artist')
                cover_url = track['album'].get('cover_medium', 'No URL')

                track_details.append({
                    'id': track_id,
                    'name': track_name,
                    'artist': artist_name,
                    'cover_url': cover_url
                })
        else:
            logger.warning("Tracks not found in response")

        return track_details

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []

# Example usage
tracks = top_tracks()
print(tracks)


def get_audio_details(query):
    url = "https://api.deezer.com/search/track"

    params = {
        "q": query,
        "limit": 1  # Limiting to 1 result to get the most relevant track
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()
        
        audio_details = []

        if 'data' in data and len(data['data']) > 0:
            track = data['data'][0]
            preview_url = track.get('preview', 'No Preview URL')
            duration = track.get('duration', 0)  # Duration is in seconds
            
            # Convert duration from seconds to a more readable format (HH:MM:SS)
            duration_text = format_duration(duration)

            audio_details.append(preview_url)
            audio_details.append(duration_text)

        else:
            print("No track data available")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    return audio_details

def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Example usage
query = "Imagine John Lennon"  # Replace with your desired track query
audio_details = get_audio_details(query)
print(audio_details)

def get_track_image(track_id, track_name):
    url = f"https://api.deezer.com/track/{track_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        data = response.json()

        # Get the cover URL (cover_medium is 300x300px size, cover_big is 600x600px size)
        cover_url = data.get('album', {}).get('cover_medium', '')

        return cover_url

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return ''

# Example usage
track_id = "123456789"  # Replace with a valid track ID from Deezer
track_name = "Imagine"  # Replace with the track name if necessary
track_image_url = get_track_image(track_id, track_name)
print(f"Track Image URL: {track_image_url}")

def music(request, pk):
    url = f"https://api.deezer.com/track/{pk}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        track_name = data.get("title", "Unknown Track")
        artist_name = data.get("artist", {}).get("name", "Unknown Artist")
        album_cover = data.get("album", {}).get("cover_medium", "")

        context = {
            'track_name': track_name,
            'artist_name': artist_name,
            'track_image': album_cover,
            # Example placeholders until you implement these functions
            'audio_url': "audio_url_placeholder",
            'duration_text': "duration_text_placeholder",
        }
        return render(request, 'music.html', context)

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return render(request, 'error.html', {'message': 'An error occurred while fetching track metadata.'})

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        return render(request, 'error.html', {'message': 'An error occurred while making a request.'})

    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return render(request, 'error.html', {'message': 'An unexpected error occurred.'})


def profile(request, pk):
    artist_id = pk

    url = f"https://api.deezer.com/artist/{artist_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        name = data.get("name", "Unknown Artist")
        monthly_listeners = data.get("nb_fan", 0)  # Assuming 'nb_fan' represents monthly listeners
        header_url = data.get("picture_medium", "")

        top_tracks = []

        if 'tracklist' in data:
            tracklist_url = data['tracklist']
            tracklist_response = requests.get(tracklist_url)
            tracklist_data = tracklist_response.json()

            for track in tracklist_data['data']:
                track_id = str(track["id"])
                track_name = track["title"]
                track_duration = track["duration"]
                track_play_count = track["rank"]

                track_image = get_track_image(track_id)

                track_info = {
                    "id": track_id,
                    "name": track_name,
                    "durationText": format_duration(track_duration),
                    "playCount": track_play_count,
                    "track_image": track_image
                }

                top_tracks.append(track_info)

        artist_data = {
            "name": name,
            "monthlyListeners": monthly_listeners,
            "headerUrl": header_url,
            "topTracks": top_tracks,
        }

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        artist_data = {}

    except Exception as ex:
        print(f"Error occurred: {ex}")
        artist_data = {}

    return render(request, 'profile.html', artist_data)


def search(request):
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')

        url = "https://api.deezer.com/search"

        params = {
            "q": search_query,
            "limit": 100,  # Limiting to 10 results, adjust as needed
            "order": "RANKING"  # Optional: You can change the order based on your preference
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            search_results_count = data.get("total", 0)
            tracks = data.get("data", [])

            track_list = []

            for track in tracks:
                track_name = track.get("title", "Unknown Track")
                artist_name = track.get("artist", {}).get("name", "Unknown Artist")
                duration = track.get("duration", 0)
                track_id = str(track.get("id", ""))

                # Fetch track image (placeholder function)
                track_image = get_track_image(track_id)

                track_list.append({
                    'track_name': track_name,
                    'artist_name': artist_name,
                    'duration': format_duration(duration),
                    'trackid': track_id,
                    'track_image': track_image,
                })

            context = {
                'search_results_count': search_results_count,
                'track_list': track_list,
            }

            return render(request, 'search.html', context)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return render(request, 'search.html', {'error_message': 'An error occurred while processing your request.'})

        except Exception as ex:
            print(f"Error occurred: {ex}")
            return render(request, 'search.html', {'error_message': 'An unexpected error occurred.'})

    else:
        return render(request, 'search.html')

def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02}"







@login_required(login_url='login')
def index(request):
    artists_info = top_artists()
    top_tracks_list = top_tracks()
    
   
    
    
    first_six_tracks = top_tracks_list[:6]
    second_six_tracks = top_tracks_list[6:12]
    third_six_tracks = top_tracks_list[12:18]

    context = {
        'artists_info':artists_info,
        'first_six_tracks':first_six_tracks,
        'second_six_tracks':second_six_tracks,
        'third_six_tracks':third_six_tracks,
    }
    return render(request,'index.html',context)

def login(request):
    if request.method =='POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = auth.authenticate(username=username, password=password)
        
        
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Credentials')
            return redirect ('login')
        
    return render(request,'login.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password == password2:
            print ('password same')
            if User.objects.filter(email=email).exists():
                messages.info(request,'Email already exists')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request,'Username already exists')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username,email=email, password=password)
                user.save()                
                
                # log user in
                
                user_login = auth.authenticate(username=username, email=email, password=password)
                auth.login(request,user_login)
                return redirect('/')
        else:
            messages.info(request,'password not matching!!!!!!!!!!!!!!')
            return redirect('signup')
        
    else:
        return render(request,'signup.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')