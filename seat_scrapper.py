import aiohttp
import asyncio

from bs4 import BeautifulSoup

from datetime import datetime

def get_term():
    
    current = datetime.now()
    month = int(current.month)
    
    season = "01" # Spring Semester
    
    if month >= 9:
        season = "09" # Fall Semester
    elif month >= 5:
        season = "05" # Summer Semester
    
    return str(current.year) + season
    

async def find_seats(crn, fixed_term="none"):
    
    term = get_term() if fixed_term == "none" else fixed_term
    
    url = f"https://sis.rpi.edu/rss/bwckschd.p_disp_detail_sched?term_in={term}&crn_in={crn}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    
    seats_left = 0
    seats_total = 0
    class_name = "UNNAMED"
    
    try:
        seating_values = soup.find(summary="This layout table is used to present the seating numbers.").find_all(class_="dddefault")
    
        seats_total = int(seating_values[0].get_text())
        seats_left = int(seating_values[2].get_text())
        
    except Exception as e:
        print(f"HTML is not formatted properly to find seating values: {e}")

    try:    
        class_name = soup.find(class_="ddlabel").get_text()
    except Exception as e:
        print(f"HTML is not formatted properly to find class_name: {e}")
        
    return {
        "name" : class_name,
        "left" : seats_left,
        "total" : seats_total
    }
    
if __name__ == "__main__":
    
    print(get_term()) # Test case 0: fetch current term
    
    print(asyncio.run(find_seats(77330))) # Test case 1: find seats with CRN on current term
    
    print(asyncio.run(find_seats(44314, "202101"))) # Test case 2: find seats with CRN on spring 
    
    print(asyncio.run(find_seats(17794, "202205"))) # Test case 3: find seats with CRN on summer 
    
    print(asyncio.run(find_seats(72024, "202509"))) # Test case 4: find seats with CRN on fall
    