# SWB
Discord bot for lobbies, requires you to install sqlite yourself.

# Commands
Commands can be split up into 2 categories, user and moderation. 
## User:
`/lobby <code> <description>`<br>
Used to create a lobby, code has to be 6 characters long. Will give you an error message if you input a different length. Any non-letters, like: `, . ? ]`, will be removed from the input. Code will be capitalised. The description can be anything, use this to specify gamemode/map/etc. 

## Moderation:
`/getlobby <code>`<br>
Used to retrieve data from a single lobby from the database. To be used with either the 6 letter match codes or the 36 character UUID's. Will respond with an error if you input anything else. Supports lower case.
Returns you the host of the match and the players who pressed the show button.

`/getlobbys <code1> <code2>`<br>
Used to retrieve data from multiple lobbies at once. Only use one type of code at the time, either the 6 letter code or the 36 character UUID. Separate the codes with a " ". The 6 letter codes support lower case. Gives you an error message if the search is invalid. Returns a .tsv file with match data. 

`/getperiod <date1> <date2 (optional)>`<br>
Used to retrieve data from matches during a specific time period. Will give you a general error message if you mess up the syntax. Any date syntax should work, as long as it's in dd/mm/yyyy format, any type of common character used to display dates work. 
There are 2 ways to use this command. The first is by using the first argument only. When using this you get every match from the input date until now. This version of the command also supports the use of relative dates: 45m, 2h, 3d. 
The second option is using the additional argument 'date2'. This version doesn't support relative dates, but lets you select matches from specific days. 
Note: When using dates, it selects, for example, 10/09/2022 0:00:00. So to get data from the 9th through the 10th, you need to use 9/09/2022 and 11/09/2022. 

`/stats`<br>
More of a fun command that show the amount of lobbies logged, aswell as the number of unique players.

## Examples:
`/lobby ASDGTH NM pods`<br>
`/lobby wed...gtf NM pods`<br>

`/getlobby asdgth`<br>
`/getlobbys ASDGTH WEDGTF`<br>

`/getperiod 45m`<br>
`/getperiod 7/9/2022`<br>
`/getperiod 6-9-2022 8/9/2022`<br>
