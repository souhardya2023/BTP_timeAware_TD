"""150 project domains.
src A = title of an idea in the public list github.com/florinpop17/app-ideas (88 ideas: 35 beginner -> S, 33 intermediate -> M, 20 advanced -> L).
src C = a classic programming-task domain added by the author of this dataset (62), to reach 150 and a wider range of sizes.
Entities: 'Name:field,field#,field?' ; '#' = numeric field, '?' = flag field, otherwise text.  Larger tiers get generic support entities added by the generator."""

RAW = """
bin2dec|Bin2Dec|S|A|Conversion:binary,decimal#,bits#;History:source_text,result,ts#
border-radius|Border Radius Previewer|S|A|Preset:name,radius#,unit;Shape:label,width#,height#
calculator|Calculator|S|A|Expression:text,result#,valid?;Memory:slot,value#
christmas-lights|Christmas Lights|S|A|Light:color,brightness#,on?;Pattern:name,delay#
cause-effect|Cause Effect App|S|A|Cause:label,weight#;Effect:label,severity#,cause
color-cycle|Color Cycle|S|A|Color:name,hexcode,hue#;Cycle:name,speed#,loop?
countdown|Countdown Timer|S|A|Timer:label,seconds#,running?;Alarm:label,sound
csv2json|CSV2JSON App|S|A|Row:raw,fields#,valid?;Doc:name,layout
dollars-cents|Dollars to Cents|S|A|Amount:currency,dollars#,cents#;Receipt:label,total#
css-variables|Dynamic CSS Variables|S|A|Variable:name,value,unit;Theme:name,active?
first-db|First DB App|S|A|Record:key,value,version#;Table:name,rows#
flip-image|Flip Image|S|A|Image:name,width#,height#,flipped?;Operation:kind,count#
github-status|GitHub Status|S|A|Service:name,status,latency#;Incident:title,severity#,resolved?
hello|Hello|S|A|Greeting:text,lang,count#;Visitor:name,visits#
iot-mailbox|IOT Mailbox Simulator|S|A|Mailbox:owner,letters#,open?;Sensor:kind,reading#
input-validation|JS Input Validation|S|A|Field:name,value,required?;Rule:kind,limit#
json2csv|JSON2CSV App|S|A|Record:raw,keys#,valid?;Output:name,delimiter
key-value|Key Value|S|A|Entry:key,value,ttl#;Store:name,size#
lorem-ipsum|Lorem Ipsum Generator|S|A|Paragraph:text,words#;Request:style,count#
notes|Notes App|S|A|Note:title,body,size#,pinned?;Tag:name,uses#
pearson|Pearson Regression|S|A|Series:name,mean#,size#;Result:label,coeff#,valid?
pomodoro|Pomodoro Clock|S|A|Session:label,minutes#,done?;Pause:kind,minutes#
landing-page|Product Landing Page|S|A|Product:name,price#,featured?;Lead:email,source
quiz|Quiz App|S|A|Question:text,answer,points#;Attempt:player,score#,passed?
recipe|Recipe App|S|A|Recipe:title,minutes#,vegan?;Ingredient:name,grams#
random-meal|Random Meal Generator|S|A|Meal:name,cuisine,calories#;Pick:label,seed#
random-number|Random Number Generator|S|A|Draw:label,low#,high#;Seed:name,value#
roman-numerals|Roman to Decimal Converter|S|A|Numeral:text,value#,valid?;Batch:name,size#
slider-design|Slider Design|S|A|Slider:label,minimum#,maximum#,locked?;Style:name,color
stopwatch|Stopwatch App|S|A|Lap:label,millis#,best?;Run:name,laps#
true-or-false|TrueOrFalse|S|A|Statement:text,difficulty#,truth?;Round:player,score#
vigenere|Vigenere Cipher|S|A|Message:text,key,encrypted?;Keyring:name,length#
wind-chill|Wind Chill|S|A|Reading:station,temp#,wind#;Report:label,count#
word-frequency|Word Frequency|S|A|Document:name,words#;Token:word,count#,stop?
weather|Weather App|S|A|City:name,temp#,humidity#,rain?;Forecast:day,high#,low#
bit-masks|Bit Masks|M|A|Mask:name,bits#,active?;Flag:label,position#;Register:name,value#
book-finder|Book Finder App|M|A|Book:title,author,pages#,available?;Shelf:label,capacity#;Query:text,hits#
calculator-cli|Calculator CLI|M|A|Token:text,kind,position#;Stack:name,depth#;Result:label,value#,ok?
card-memory|Card Memory Game|M|A|Card:face,suit,flipped?;Board:name,size#,moves#;Player:name,score#
charity-finder|Charity Finder App|M|A|Charity:name,cause,rating#,verified?;Donation:donor,amount#;Region:name,count#
chrome-theme|Chrome Theme Extension|M|A|Theme:name,accent,contrast#,dark?;Tab:title,url,visits#;Setting:key,value
currency-converter|Currency Converter|M|A|Currency:code,rate#,active?;Quote:pair,amount#,spread#;Wallet:owner,balance#
drawing-app|Drawing App|M|A|Stroke:color,width#,erased?;Canvas:title,width#,height#;Tool:name,size#
emoji-translator|Emoji Translator App|M|A|Emoji:symbol,word,uses#,popular?;Phrase:text,length#;Dictionary:name,entries#
flashcards|Flashcards App|M|A|Card:front,back,box#,known?;Deck:title,size#;Review:learner,streak#
flip-art|Flip Art App|M|A|Frame:label,index#,keyframe?;Animation:title,fps#;Layer:name,opacity#
game-suggestion|Game Suggestion App|M|A|Game:title,genre,rating#,multiplayer?;Profile:player,hours#;Suggestion:label,score#
github-profiles|GitHub Profiles|M|A|Profile:login,followers#,hireable?;Repo:name,stars#,language;Summary:label,total#
high-striker|HighStriker Game|M|A|Strike:player,force#,hit?;Meter:label,level#,max#;Score:player,total#
image-scanner|Image Scanner|M|A|Scan:name,pixels#,clean?;Region:label,area#;Report:title,findings#
markdown-previewer|Markdown Previewer|M|A|Block:text,kind,level#,closed?;Document:title,blocks#;Style:name,size#
markdown-table|Markdown Table Generator|M|A|Cell:text,column#,header?;Table:title,rows#,columns#;Align:name,width#
math-editor|Math Editor|M|A|Formula:text,depth#,valid?;Symbol:name,glyph,uses#;Variable:name,value#
meme-generator|Meme Generator App|M|A|Meme:caption,template,likes#,safe?;Template:name,width#,height#;Font:name,size#
name-generator|Name Generation using RNNs|M|A|Sample:text,length#,novel?;Corpus:name,size#;Model:label,loss#
password-generator|Password Generator|M|A|Password:value,length#,strong?;Policy:name,minimum#;Vault:owner,entries#
podcast-directory|Podcast Directory|M|A|Podcast:title,host,episodes#,active?;Episode:name,minutes#;Category:label,count#
qr-badge|QR Code Badge Generator|M|A|Badge:holder,code,level#,printed?;Event:name,capacity#;Template:label,size#
regex-helper|Regular Expression Helper|M|A|Pattern:text,flags,matches#,valid?;Sample:text,length#;Library:name,size#
sales-receipts|Sales Receipts App|M|A|Receipt:customer,total#,paid?;Line:item,quantity#,price#;Register:name,balance#
online-store|Simple Online Store|M|A|Product:name,price#,stock#,listed?;Cart:owner,items#;Order:customer,total#,shipped?
sports-bracket|Sports Bracket Generator|M|A|Team:name,seed#,eliminated?;Match:label,round#,winner;Bracket:title,size#
string-art|String Art|M|A|Nail:label,x#,y#;Thread:color,length#,placed?;Board:name,nails#
this-or-that|This or That Game|M|A|Choice:left,right,votes#,open?;Player:name,points#;Round:label,number#
timezone-bot|Timezone Slackbot|M|A|Zone:name,offset#,dst?;Member:handle,zone;Reminder:text,minutes#
todo|To-Do App|M|A|Task:title,priority#,done?;Project:name,tasks#;Label:name,color
typing-practice|Typing Practice|M|A|Passage:text,words#,hard?;Attempt:player,speed#,errors#;Stats:label,best#
voting|Voting App|M|A|Candidate:name,votes#,withdrawn?;Ballot:voter,choice,valid?;Election:title,open#
battleship-bot|Battleship Bot|L|A|Ship:name,size#,sunk?;Shot:row#,col#,hit?;Board:owner,cells#;Strategy:label,depth#
battleship-engine|Battleship Game Engine|L|A|Fleet:owner,ships#,ready?;Turn:player,number#;Grid:label,size#;Result:winner,turns#
boole-bots|Boole Bots Game|L|A|Bot:name,energy#,alive?;Gate:kind,inputs#;Arena:label,size#;Match:round#,winner
calendar|Calendar|L|A|Event:title,start#,duration#,recurring?;Reminder:text,minutes#;Calendar:owner,events#;Invite:guest,status
calorie-counter|Calorie Counter|L|A|Meal:name,calories#,logged?;Food:name,protein#,fat#;Goal:owner,target#;Day:label,total#
chat-app|Chat App|L|A|Message:body,sender,length#,read?;Room:name,members#;Account:handle,karma#,online?;Thread:topic,replies#
contribution-tracker|Contribution Tracker App|L|A|Contribution:author,lines#,merged?;Repo:name,stars#;Streak:author,days#;Badge:label,level#
elevator|Elevator|L|A|Car:label,floor#,moving?;Request:origin#,target#;Shaft:name,height#;Log:event,ts#
fast-food|Fast Food Simulator|L|A|Order:customer,total#,ready?;Item:name,price#,prep#;Station:label,load#;Shift:worker,hours#
instagram-clone|Instagram Clone|L|A|Post:caption,likes#,flagged?;Profile:handle,followers#;Comment:text,length#;Feed:owner,size#
github-timeline|GitHub Timeline|L|A|Commit:message,author,additions#,merge?;Branch:name,commits#;Release:tag,date#;Contributor:login,total#
kudos-bot|Kudos Slackbot|L|A|Kudos:giver,receiver,points#,public?;Channel:name,members#;Member:handle,balance#;Leaderboard:label,size#
movie-app|Movie App|L|A|Movie:title,year#,rating#,released?;Actor:name,movies#;Review:author,stars#;Watchlist:owner,size#
my-podcast-library|MyPodcast Library|L|A|Show:title,episodes#,subscribed?;Episode:name,minutes#,played?;Playlist:label,size#;Download:file,bytes#
exoplanet-query|NASA Exoplanet Query|L|A|Planet:name,radius#,mass#,habitable?;Star:name,temperature#;Survey:label,count#;Query:text,hits#
shell-game|Shell Game|L|A|Shell:position#,hidden?;Round:player,number#;Player:name,wins#;Bet:amount#,paid?
shuffle-deck|Shuffle Deck|L|A|Card:rank,suit,value#,dealt?;Deck:label,count#;Hand:player,total#;Shuffle:method,passes#
slack-archiver|Slack Archiver|L|A|Archive:channel,messages#,exported?;Message:body,author,size#;Export:file,bytes#;Member:handle,posts#
spell-it|Spell-It App|L|A|Word:text,length#,hard?;Attempt:player,errors#,correct?;Lesson:title,words#;Learner:name,streak#
survey|Survey App|L|A|Question:text,kind,required?;Answer:respondent,value#;Survey:title,responses#;Respondent:email,completed?
fizzbuzz-rules|FizzBuzz Rules Engine|S|C|Rule:divisor#,label,active?;Run:name,count#
temperature-converter|Temperature Converter|S|C|Reading:scale,degrees#,valid?;Table:name,rows#
anagram-finder|Anagram Finder|S|C|Word:text,length#,common?;Group:key,size#
palindrome|Palindrome Checker|S|C|Phrase:text,length#,palindrome?;Report:label,hits#
prime-sieve|Prime Sieve|S|C|Candidate:value#,prime?;Sieve:name,limit#
tip-calculator|Tip Calculator|S|C|Bill:diner,amount#,paid?;Split:label,people#
unit-converter|Unit Converter|S|C|Unit:name,factor#,metric?;Conversion:label,amount#
caesar-cipher|Caesar Cipher|S|C|Message:text,shift#,encoded?;Alphabet:name,size#
fibonacci-memo|Fibonacci Memo|S|C|Term:index#,value#,cached?;Cache:name,hits#
number-guess|Number Guessing Game|S|C|Guess:player,value#,correct?;Game:label,secret#
rock-paper-scissors|Rock Paper Scissors|S|C|Move:player,shape,beats?;Match:label,rounds#
hangman|Hangman|S|C|Word:text,length#,solved?;Game:player,lives#
dice-roller|Dice Roller|S|C|Roll:label,sides#,result#;Session:player,rolls#,lucky?
coin-change|Coin Change|S|C|Coin:name,value#,rare?;Change:label,total#
mortgage-calculator|Mortgage Calculator|S|C|Loan:borrower,principal#,rate#,fixed?;Payment:label,amount#
library-management|Library Management|M|C|Book:title,author,copies#,reserved?;Member:name,email,fines#;Loan:book,member,days#
hotel-booking|Hotel Booking|M|C|Room:number,category,price#,occupied?;Guest:name,email,nights#;Booking:room,guest,total#
parking-lot|Parking Lot|M|C|Slot:label,level#,free?;Vehicle:plate,kind,hours#;Ticket:plate,fee#,paid?
bank-ledger|Bank Ledger|M|C|Account:owner,balance#,frozen?;Entry:account,amount#,memo;Statement:label,total#
inventory|Inventory Tracker|M|C|Item:sku,name,quantity#,discontinued?;Supplier:name,rating#;Movement:item,delta#
payroll|Payroll|M|C|Employee:name,department,salary#,active?;Payslip:employee,net#,issued?;Deduction:label,rate#
clinic-appointments|Clinic Appointments|M|C|Patient:name,phone,age#,insured?;Doctor:name,specialty,load#;Appointment:patient,slot#,confirmed?
course-registration|Course Registration|M|C|Course:code,title,seats#,open?;Student:name,credits#;Enrollment:course,student,grade#
url-shortener|URL Shortener|M|C|Link:target,code,clicks#,expired?;Owner:email,links#;Visit:code,ts#
pastebin|Pastebin|M|C|Paste:title,body,views#,private?;Author:name,pastes#;Report:paste,reason
expense-splitter|Expense Splitter|M|C|Expense:payer,amount#,settled?;Member:name,balance#;Group:title,size#
budget-planner|Budget Planner|M|C|Category:name,limit#,spent#,over?;Income:source,amount#;Plan:month,total#
invoice-generator|Invoice Generator|M|C|Invoice:client,total#,sent?;Line:description,hours#,rate#;Client:name,terms#
time-tracker|Time Tracker|M|C|Entry:task,minutes#,billable?;Project:name,budget#;Worker:name,rate#
habit-tracker|Habit Tracker|M|C|Habit:title,streak#,active?;Check:habit,day#,done?;Goal:label,target#
grocery-list|Grocery List|M|C|Product:name,aisle,price#,bought?;Store:name,distance#;Basket:owner,items#
event-rsvp|Event RSVP|M|C|Event:title,venue,capacity#,open?;Guest:name,email,party#;Reply:guest,status
gym-membership|Gym Membership|M|C|Member:name,plan,visits#,active?;Plan:title,fee#;Visit:member,minutes#
car-rental|Car Rental|M|C|Car:plate,model,daily#,available?;Customer:name,licence,rentals#;Rental:car,days#
cinema-booking|Movie Ticket Booking|M|C|Show:title,hall,seats#,sold_out?;Ticket:seat#,price#,used?;Viewer:name,visits#
help-desk|Help Desk Tickets|M|C|Ticket:title,priority#,agent,closed?;Agent:name,open#;Reply:ticket,length#
bug-tracker|Bug Tracker|M|C|Bug:title,severity#,reporter,fixed?;Release:tag,open#;Developer:name,assigned#
log-analyzer|Log Analyzer|M|C|Entry:level,message,count#,error?;Source:name,lines#;Alert:rule,threshold#
rate-limiter|Rate Limiter|M|C|Client:key,requests#,blocked?;Rule:route,limit#;Window:label,seconds#
task-scheduler|Task Scheduler|M|C|Job:name,interval#,priority#,paused?;Run:job,duration#,failed?;Worker:name,load#
vending-machine|Vending Machine|M|C|Slot:code,product,price#,empty?;Coin:value#,count#;Sale:code,paid#
atm-machine|ATM Machine|M|C|Card:holder,limit#,blocked?;Withdrawal:card,amount#;Cassette:note#,count#
shopping-cart|E-commerce Cart and Checkout|L|C|Product:sku,name,price#,in_stock?;Cart:owner,lines#;Coupon:code,percent#,used?;Order:customer,total#,paid?
warehouse-picking|Warehouse Picking|L|C|Bin:label,aisle#,stock#,full?;Order:number,lines#,packed?;Picker:name,rate#;Route:label,steps#
ride-dispatch|Ride Dispatch|L|C|Driver:name,rating#,available?;Rider:name,trips#;Trip:origin,fare#,done?;Zone:label,demand#
airline-reservation|Airline Reservation|L|C|Flight:code,origin,seats#,delayed?;Passenger:name,passport,miles#;Booking:flight,fare#,checked_in?;Fare:label,amount#
hospital-records|Hospital Records|L|C|Patient:name,ward,age#,discharged?;Visit:patient,days#;Prescription:drug,dose#,active?;Nurse:name,shift#
stock-portfolio|Stock Portfolio|L|C|Holding:symbol,shares#,cost#,sold?;Quote:symbol,price#;Trade:holding,fee#;Portfolio:owner,value#
ci-pipeline|CI Pipeline Runner|L|C|Stage:name,seconds#,passed?;Build:commit,number#;Artifact:file,bytes#;Runner:label,load#
smart-home|Smart Home Rules|L|C|Device:name,room,power#,online?;Rule:trigger,threshold#,enabled?;Scene:label,devices#;Reading:device,value#
tournament-scheduler|Tournament Scheduler|L|C|Team:name,rating#,withdrawn?;Fixture:home,away,round#;Venue:label,capacity#;Standing:team,points#
auction-house|Auction House|L|C|Lot:title,reserve#,sold?;Bid:bidder,amount#;Bidder:name,credit#,banned?;Auction:label,lots#
food-delivery|Food Delivery|L|C|Restaurant:name,rating#,open?;Dish:name,price#;Courier:name,deliveries#;Delivery:address,fee#,late?
online-exams|Online Exams|L|C|Exam:title,minutes#,published?;Question:text,marks#;Candidate:name,attempts#;Result:candidate,score#,passed?
learning-platform|Learning Management System|X|C|Course:title,hours#,published?;Lesson:name,minutes#;Learner:name,progress#,active?;Quiz:title,pass_mark#;Certificate:learner,issued?
banking-core|Banking Core|X|C|Account:owner,balance#,frozen?;Transfer:source,amount#,settled?;Customer:name,risk#;Loan:customer,principal#,overdue?;Branch:name,staff#
erp-mini|ERP Mini|X|C|Vendor:name,rating#,approved?;Purchase:vendor,total#,received?;Stock:sku,quantity#;Employee:name,salary#,active?;Ledger:account,balance#
logistics-tracking|Logistics Tracking|X|C|Shipment:code,weight#,delivered?;Hub:name,load#;Truck:plate,capacity#,idle?;Route:label,distance#;Scan:code,ts#
social-feed|Social Network Feed|X|C|Post:text,likes#,reported?;Profile:handle,followers#,verified?;Follow:source,weight#;Story:caption,views#;Ad:label,budget#
cms|Content Management System|X|C|Article:title,words#,published?;Author:name,articles#;Media:file,bytes#;Comment:text,length#,approved?;Menu:label,items#
telecom-billing|Telecom Billing|X|C|Subscriber:number,plan,balance#,active?;Call:caller,seconds#,roaming?;Tariff:label,rate#;Invoice:subscriber,total#,paid?;Tower:name,load#
hotel-chain|Hotel Chain Management|X|C|Hotel:name,rooms#,open?;Reservation:guest,nights#,cancelled?;Staff:name,wage#;Supplier:name,rating#;Review:guest,stars#
"""

TIER_NAMES = {"S": "small", "M": "medium", "L": "large", "X": "xlarge"}


def load():
    out = []
    for line in RAW.strip().splitlines():
        slug, title, tier, src, ents = line.split("|")
        entities = []
        for e in ents.split(";"):
            name, fields = e.split(":")
            fl = []
            for f in fields.split(","):
                kind = "n" if f.endswith("#") else "b" if f.endswith("?") else "s"
                fl.append((f.rstrip("#?"), kind))
            kinds = {k for _, k in fl}
            names = {f for f, _ in fl}
            if "s" not in kinds:                       # every entity gets at least one text and one numeric field
                fl.insert(0, ("label" if "label" not in names else "caption", "s"))
            if "n" not in kinds:
                fl.append(("amount" if "amount" not in names else "units", "n"))
            entities.append((name, fl))
        out.append(dict(slug=slug, title=title, tier=tier, src=src, entities=entities))
    return out


if __name__ == "__main__":
    d = load()
    import collections
    print(len(d), collections.Counter(x["tier"] for x in d), collections.Counter(x["src"] for x in d))
    assert len({x["slug"] for x in d}) == len(d)
    for x in d:
        for n, fl in x["entities"]:
            kinds = {k for _, k in fl}
            assert "s" in kinds and "n" in kinds, (x["slug"], n)
            names = [f for f, _ in fl]
            assert len(set(names)) == len(names), (x["slug"], n)
