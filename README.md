# Get notified when a crime or incident takes place near your location
This is a python script that sends alerts based on activity from Metro Nashville's Active Dispatch.
https://www.nashville.gov/departments/police/online-resources/active-dispatches

Steps to implement:

1. Setup "2-Step Verification" on your Google account using these steps [here.](https://gist.github.com/darwin/ee9e7855882b6f6b450fe45e9a5aa0b0?permalink_comment_id=4567140#gistcomment-4567140)
2. Insert your email address and password from step 1 above into the "send email" function.
3. Insert a physical address and set the distance threshold (current distance is set to half a mile).
4. Place recipient email address at the end of the script.

To automate:

Save or download the script as a .py file. I'm currently running it as a CRON job on my computer every 30 minutes. 
Follow these steps [here.](https://www.jcchouinard.com/python-automation-with-cron-on-mac/)

If this is too much work, you can check out real time alerts on my [app.](https://github.com/RodNSS/Nashville_Active_Incident_Map)

The script currently uses email for alerts as I found Verizon's email to text service "@vtext.com" unreliable and slow. Will try to 
optimize with texting capability when I have time.
