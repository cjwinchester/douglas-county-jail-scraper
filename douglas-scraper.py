"""

Who's in the Douglas County Jail?

"""

from mechanize import Browser
from bs4 import *
from time import *
import re
import gspread
import datetime

# today
today = str(datetime.date.today().strftime("%m-%d-%Y"))

# yesterday
yesterday = str((datetime.date.today() - datetime.timedelta(1)).strftime("%m-%d-%Y"))

# log in to google
gc = gspread.login('worldheraldreporting@gmail.com', 'WilfordBrimleysMu$t@che')

# open the spreadsheet
wks = gc.open("douglas jail scraper")

# create a new worksheet
wks.add_worksheet(title=today, rows="1", cols="15")

# delete yesterday's worksheet
yesterdaysheet = wks.worksheet(yesterday)
wks.del_worksheet(yesterdaysheet)

# select today's worksheet
worksheet = wks.worksheet(today)

# add headers to worksheet
worksheet.append_row(["id","last","rest","crime","age","sex","race","height","weight","facil","admissiondate","admissiontime","bond","fines","howfresh"])

# open a file to write to
f = open('douglas-booked-' + today + '.txt', 'wb')

# add headers
f.write('id|last|rest|crime|age|sex|race|height|weight|facility|admission-date|admission-time|bond|fines|how-fresh\n')

# crank up a browser
mech = Browser()

# add a user-agent string
mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

# ignore robots
mech.set_handle_robots(False)

# define opening url
baseurl = "http://www.dccorr.com/corrections/accepted"

# beautifulsoup that bizzo
page = mech.open(baseurl)
html = page.read()
soup = BeautifulSoup(html)

letters = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')

for thing in letters:
	# select the correct form on the page
    mech.select_form(nr=1)
	
	# fill out the form
    mech.form['lname'] = thing
	
	# submit and read in the results page
    req = mech.submit()
    resultspage = req.read()
	
	# soup the results page
    soup = BeautifulSoup(resultspage)

    # check to see if the search returned any records
    error = re.compile(r'No results matched your query')
    if error.search(str(soup)):
        print 'Nobody in DCCC has a last name that starts with ' + thing.upper()
        sleep(3)
        mech.back()
        continue
    else:
        pass
        print 'Processing data for inmates whose names start with ' + thing.upper() + '...\n\n'
    
    # grab the links for each inmate's detail page
    inmatelinks = []
    for link in mech.links(url_regex='inmate-details\?datanum'):
        inmatelinks.append(link.url)
    
    # loop through each detail page, collecting data
    for url in inmatelinks:
        page = mech.open(url)
        html = page.read()
        soup = BeautifulSoup(html)
        table = soup.find('table', class_='presult')

        # id
        findid = re.search('Data Number:</strong>\s\d+', str(table))
        id = findid.group().replace("Data Number:</strong> ","")

        # admission date and time
        findadmission = re.search('<strong>Admission Date - Time:</strong>\s\d\d/\d\d/\d\d\d\d - \d\d:\d\d', str(table))
        admission = findadmission.group().replace('<strong>Admission Date - Time:</strong> ','')
        admissiondate = admission.split(' - ')[0].strip()
        admissiontime = admission.split(' - ')[1].strip()

        # name
        findname = re.search('<strong>Name</strong><br/>[-,a-zA-Z\s]+', str(table))
        name = findname.group().replace('<strong>Name</strong><br/>','')
        rest = name.split(',')[1].strip()
        last = name.split(',')[0].strip()
        print 'Pulling record for ' + rest + " " + last

        # sex
        findsex = re.search('<strong>Sex</strong><br/>[a-zA-Z]+', str(table))
        sex = findsex.group().replace('<strong>Sex</strong><br/>','')

        # race
        findrace = re.search('<strong>Race</strong><br/>[a-zA-Z]+', str(table))
        race = findrace.group().replace('<strong>Race</strong><br/>','')

        # age
        findage = re.search('<strong>Age</strong><br/>[0-9]+', str(table))
        age = findage.group().replace('<strong>Age</strong><br/>','')

        # height
        findheight = re.search('<strong>Height</strong><br/>[\'"0-9]+', str(table))
        height = findheight.group().replace('<strong>Height</strong><br/>','')

        # weight
        findweight = re.search('<strong>Weight</strong><br/>[0-9a-zA-Z\s]+', str(table))
        weight = findweight.group().replace('<strong>Weight</strong><br/>','').replace(' lb','')
        
        # facility
        findfacil = re.search('<strong>Facility</strong><br/>[-0-9a-zA-Z\s]+', str(table))
        facility = findfacil.group().replace('<strong>Facility</strong><br/>','').strip()

        # charges
        findcharges = re.search('<strong>Charges</strong><br/>[<>/\$0-9a-zA-Z\s]+', str(table))
        charges = findcharges.group().replace('<strong>Charges</strong><br/>','').replace("<br/>",", ").replace("</td>","").replace("<td colspan","").strip()

        # bond
        findbond = re.search('<strong>Bond Amount</strong><br/>[/\$\(\)\%,0-9a-zA-Z\s]+', str(table))
        bond = findbond.group().replace('<strong>Bond Amount</strong><br/>','')

        # fines and costs
        findfines = re.search('<strong>Fines &amp; Costs:</strong>\s[\$\.,\%0-9a-zA-Z\s]+', str(table))
        fines = findfines.group().replace('<strong>Fines &amp; Costs:</strong>','').strip()

        # freshness
        findfresh = re.search('Data current as of \d\d/\d\d/\d\d\d\d', str(soup))
        fresh = findfresh.group().replace('Data current as of ','').strip()
        
        # put it all together
        fullrecord = (id, last, rest, charges, age, sex, race, height, weight, facility, admissiondate, admissiontime, bond, fines, fresh)
        
        # write it to our spreadsheet
        worksheet.append_row(fullrecord)
        
        # write it to our file
        f.write("|".join(fullrecord))
        
        print "Success! Record written. Going back for more...\n"
        
        # navigate back
        mech.back()
        sleep(1)
        
    page = mech.open(baseurl)
    sleep(1)
    html = page.read()
    soup = BeautifulSoup(html)

f.close()
