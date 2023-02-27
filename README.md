# LinkedInDumper
Python 3 script to dump company employees from LinkedIn Voyager API.

The results contain firstname, lastname, position (title), location and a user's profile link. Only 2 API calls are required to retrieve all employees if the company does not have more than 10 employees. Otherwise, we have to paginate through the API results. With the `--email-format` CLI flag one can define a Python string format to auto generate email addresses based on the retrieved first and last name.

## Limitations

LinkedIn will allow only the first 1,000 search results to be returned when harvesting contact information. You may also need a LinkedIn premium account when you reached the maximum allowed queries for visiting profiles with your freemium LinkedIn account.

Furthermore, not all employee profiles are public. The results vary depending on your used LinkedIn account and whether you are befriended with some employees of the company to crawl or not. Therefore, it is sometimes not possible to retrieve the firstname, lastname and profile url of some employee accounts. The script will not display such profiles, as they contain default values such as "LinkedIn" as firstname and "Member" in the lastname. If you want to include such private profiles, please use the CLI flag ``--include-private-profiles``. Although some accounts may be private, we can obtain the position (title) as well as the location of such accounts. Only firstname, lastname and profile URL are hidden for private LinkedIn accounts.

Finally, LinkedIn users are free to name their profile. An account name can therefore consist of various things such as saluations, abbreviations, emojis, middle names etc. I tried my best to remove some nonsense. However, this is not a complete solution to the general problem. Note that we are not using the official LinkedIn API. This script gathers information from the "unofficial" Voyager API.
 
## How-To
1. Sign into www.linkedin.com and retrieve your ``li_at`` session cookie value e.g. via developer tools. I recommend not using your real LinkedIn account.
2. Specify the cookie value either persistently in the python script's variable ``li_at`` or temporarily via the CLI flag ``--cookie``
3. Browse your company on LinkedIn and note the url. Must be something like https://www.linkedin.com/company/apple
4. Install requirements via ``pip install -r requirements.txt``
5. Run the Python script and enjoy results

## Usage
````
usage: linkedindumper.py [-h] --url <linkedin-url> [--cookie <cookie>] [--quiet] [--include-private-profiles] [--email-format EMAIL_FORMAT]

options:
  -h, --help            show this help message and exit
  --url <linkedin-url>  A LinkedIn company url - https://www.linkedin.com/company/<company>
  --cookie <cookie>     LinkedIn 'li_at' session cookie
  --quiet               Show employee results only
  --include-private-profiles
                        Show private accounts too
  --email-format        Python string format for emails; for example:
                         [1] john.doe@example.com > '{0}.{1}@example.com'
                         [2] j.doe@example.com > '{0[0]}.{1}@example.com'
                         [3] jdoe@example.com > '{0[0]}{1}@example.com'
                         [4] doe@example.com > '{1}@example.com'
                         [5] john@example.com > '{0}@example.com'
                         [6] jd@example.com > '{0[0]}{1[0]}@example.com'
````

## Docker Run Examples

````
docker run --rm l4rm4nd/linkedindumper:latest --url <linkedin-url> --cookie <cookie> --email-format '{0}.{1}@example.com'
````

## Examples

Dumping Apple employees from LinkedIn API into outfile using `--quiet` mode:
````
python3 linkedindumper.py --url 'https://www.linkedin.com/company/apple' --quiet --email-format '{0}.{1}@apple.com' > apple_employees.out
````

## Results

The script will return employee data as semi-colon separated values (like CSV):

````
 ██▓     ██▓ ███▄    █  ██ ▄█▀▓█████ ▓█████▄  ██▓ ███▄    █ ▓█████▄  █    ██  ███▄ ▄███▓ ██▓███  ▓█████  ██▀███  
▓██▒    ▓██▒ ██ ▀█   █  ██▄█▒ ▓█   ▀ ▒██▀ ██▌▓██▒ ██ ▀█   █ ▒██▀ ██▌ ██  ▓██▒▓██▒▀█▀ ██▒▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▒██░    ▒██▒▓██  ▀█ ██▒▓███▄░ ▒███   ░██   █▌▒██▒▓██  ▀█ ██▒░██   █▌▓██  ▒██░▓██    ▓██░▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▒██░    ░██░▓██▒  ▐▌██▒▓██ █▄ ▒▓█  ▄ ░▓█▄   ▌░██░▓██▒  ▐▌██▒░▓█▄   ▌▓▓█  ░██░▒██    ▒██ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
░██████▒░██░▒██░   ▓██░▒██▒ █▄░▒████▒░▒████▓ ░██░▒██░   ▓██░░▒████▓ ▒▒█████▓ ▒██▒   ░██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░ ▒░▓  ░░▓  ░ ▒░   ▒ ▒ ▒ ▒▒ ▓▒░░ ▒░ ░ ▒▒▓  ▒ ░▓  ░ ▒░   ▒ ▒  ▒▒▓  ▒ ░▒▓▒ ▒ ▒ ░ ▒░   ░  ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
░ ░ ▒  ░ ▒ ░░ ░░   ░ ▒░░ ░▒ ▒░ ░ ░  ░ ░ ▒  ▒  ▒ ░░ ░░   ░ ▒░ ░ ▒  ▒ ░░▒░ ░ ░ ░  ░      ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░
  ░ ░    ▒ ░   ░   ░ ░ ░ ░░ ░    ░    ░ ░  ░  ▒ ░   ░   ░ ░  ░ ░  ░  ░░░ ░ ░ ░      ░   ░░          ░     ░░   ░ 
    ░  ░ ░           ░ ░  ░      ░  ░   ░     ░           ░    ░       ░            ░               ░  ░   ░     
                                      ░                      ░                                         ░ by LRVT      

[i] Company Name: apple
[i] Company X-ID: 162479
[i] LN Employees: 1000 employees found
[i] Dumping Date: 17/10/2022 13:55:06
[i] Email Format: {0}.{1}@apple.de

Firstname;Lastname;Email;Position;Gender;Location;Profile
Katrin;Honauer;katrin.honauer@apple.com;Software Engineer at Apple;N/A;Heidelberg;https://www.linkedin.com/in/katrin-honauer
Raymond;Chen;raymond.chen@apple.com;Recruiting at Apple;N/A;Austin, Texas Metropolitan Area;https://www.linkedin.com/in/raytherecruiter

[i] Successfully crawled 2 unique apple employee(s). Hurray ^_-
````
