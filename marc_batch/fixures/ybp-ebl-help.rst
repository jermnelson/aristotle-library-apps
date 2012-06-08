Loading EBL/DDA records for Alliance pilot project
--------------------------------------------------
Before begining, Edit Millennium template as noted below with appropriate values:

    Bib template (use FAC) - change to today's date, loc = ewwwn, 
    bcode 3 = e, material type = a
    
    Do not need to edit leader in template
    
    Item template (use bcri/FAC)- Icode 2 = e, Itype = 32, loc = ewwwn, status=j
	
	
Open Filezilla:

    FTP domain name: **ftp.ybp.com** (host)
    
    FTP User ID: **coalliance (username)**
    
    FTP Password: **M#22kn (quickconnect)**
    
    FTP subdirectory: **DDA (select)**
    
    Path: **coalliance\DDA  (select)**
    
Find Newest DDA file and drag to desktop folder on lower left portion of ftp software (filezilla). Close.

(On Desktop) open file in the desktop folder on the desktop

Open Firefox. Go to tuttlibsys/apps

Marc Batch

Click DDA in legacy

Browse/select file from desktop folder on desktop/open

Choose Bibliographic records/ Upload

Download modified Marc file.

Save - leave file name as is.

Open in MarcEdit/Execute/Edit

Review sample records for alliance practices. Run MarcEdit checks and 
repairs per Betty's instructions (call numbers are removed in load table 
so no need to check them over at this time)

Save.

Compile into Marc

Save. (Look for purple mrc file in desktop folder save again and 
replace - fine to keep same file name)

In Millennium, go to Data Exchange (DE)

Load bib records from tape or fts (local).

Get PC. Look on Desktop to find dda .mrc file (purple)/all files. 
(job-YBP_EBL_DDA_load date)

Upload. Change suffix to .lfts. Ok. Click last modified column twice to 
bring to top.

Highlight Lfts file/prep/start.

Confirm record numbers - input and output at bottom of screen should be 
the same and they should match the original number of records. Close

Click last modified column 2xs again/Choose Lmarc file

Load L - write down start block and stop block number

**CHECK USE REVIEW FILE**

Test/confirm no errors/if all looks good, 
Load. Write down on sheet new records, overlaid records, rejected 
records, and bib record start and stop numbers. Highlight and copy 
(click at bottom, shift, click at top, ctrl-c). Do not close DE. 

Paste in tuttlibsys note value. Record # of new records, overlaid recs, 
rejected recs.

In Create Lists, find 2 review files large enough, one for bibs, one for items

Copy, "Load: inserted records...job-YBP....dda..."/Yes.

Rename DDA EBL Update #, load date.

Also make a create list for overlaid records. Copy, Overlaid: for any 
overlaid so can delete second item record from review file. Rename DDA 
EBL overlaid update #, load date.

Check bib records. Check diacritics.

Make item list from bib list. Global Update Insert Marc Tag 099 - DDA EBL

Perform any other fixes in global update.

Record statistics in app
