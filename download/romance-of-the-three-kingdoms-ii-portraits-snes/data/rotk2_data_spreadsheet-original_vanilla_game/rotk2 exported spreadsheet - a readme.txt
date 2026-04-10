rotk2 exported spreadsheet - notes
October 25th.

The following can be ignored if the data spreadsheet is only being used as a stats reference.

These notes are very incomplete.


- Negative one `-1` is often used as a False / null value (e.g. to represent the number 255, or to represent an empty province).
- For a vanilla-structured rom all of the extra portrait palette values are simply ignored (The maximum number of unique portraits allowed in vanilla is around 236 or so, whereas in the Darkmoon Expander framework the max is 2000).
- Note well: The six column officer-provinces tab uses zero indexed values (which is how it is in the rom) whereas other sheets use one-indexing (how provinces appear in-game).
- The name converter is currently strict about what names are allowed. A name that does not meet the criteria is given the name `UNABLE` (or something similar, depending on the current tool version).  For example, the name `Augustus` would not pass the test that the first name must have <= 7 characters. I am going to allow an option for less strictness since Darkmoon added a tweak to allow for longer names.
- Names can only be be changed in the dedicated names sheet tab.  All other cells with a copy of the name are formula references (and are ignored by the utility).
- When converting from a spreadsheet to a rom, the tool can infer certain details. For example, the faction count of a scenario will be updated in the rom automatically based on the number of factions (e.g. not `-1`). The tool also updates the starting points for the immediate and later chains. Etc.
- There are a couple places where the immediate chain overrides other stats for an officer. This is intended as a convenience. So if an officer is placed somewhere in an immediate chain, the utility will automatically override the officer's province value for the relevant scenario.  This allows users to move officers around in the immediate-chain tab without having to also manually update the relevant cell in the province tab.  Currently the utility will also ensure that no immediate-chain officer has a loyalty greater than 100 (so if you add an officer to the immediate chain, you don't have to worry about him having a 255 loyalty value).  This override step occurs when the spreadsheet is converted into a rom.
- In the spreadsheet the word 'hidden' means 'unemployed' rather than a spy or mole. I'm probably going to pick a different word for it.
- For a darkmoon-expander-framework-structured mod, the quantity of officers is determined by looking for where the first blank row appears in the officer stats sheet.
- IIRC: for the later chains, the spreadsheet export tool is currently more tolerant than the snes game. For example, if Lu Bu is somewhere in the later chain and has an active date of 220, but he comes after a year 235 officer in the later chain, then the tool will move Lu Bu to the year 220 section before exporting to the spreadsheet.  I believe the snes game simply skips over officers in this situation.  This is only relevant for exporting to a spreadsheet; importing from the spreadsheet back into the rom takes care of everything.
