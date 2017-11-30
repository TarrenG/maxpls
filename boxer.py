import os, requests, itertools, re, difflib, requests_cache, time
from bs4 import BeautifulSoup
from collections import OrderedDict

"""
scrape boxrec with requests + bs4
by: Tarren Grimsley
"""

requests_cache.install_cache(cache_name='boxrec_cache', backend='sqlite', expire_after=86400)


def get_request(boxer):
    """ make the intial request, or retrieve from cache and return response and best matched name """
    result = ""
    #http://boxrec.com/en/search?pf[first_name]=errol&pf[last_name]=spence%20jr
    result = ""
    best_match_name = ""
    try:
        if (str.isdigit(boxer)):
            result = requests.get("http://boxrec.com/en/boxer/%s" % boxer)
            soup = BeautifulSoup(result.content, "lxml")
            best_match_name = soup.find_all("h1")[0].text
            print("best_match_name in isdigit %s" % best_match_name)
            return result, best_match_name
        else:
            first_name = boxer.split(" ")[0]
            last_name = " ".join(boxer.split(" ")[1:])
            url = "http://boxrec.com/en/search?pf[role]=boxer&pf[first_name]=%s&pf[last_name]=%s" % (first_name, last_name)
            print("url: %s" % url)
            result = requests.get(url)
            soup = BeautifulSoup(result.content, "lxml")
            table = soup.find_all("table", "dataTable")
            name_dict = {}
            for item in table:
                names = item.find_all("a", "personLink")
                career_wins = item.find_all("span", "textWon")
                for name, wins in zip(names,career_wins):
                    name_dict[name.text.strip()] = name['href']
                    print(name.text.strip(), wins.text.strip() , name['href'])
            best_match = name_dict[difflib.get_close_matches(boxer,name_dict.keys())[0]]
            best_match_name = difflib.get_close_matches(boxer,name_dict.keys())[0]
            boxrec_url = "http://boxrec.com%s" % best_match
            result = requests.get(boxrec_url)
            #print("\nUsed Cache: {1}\n".format(time.time, result.from_cache))
            print("returning",result, best_match_name)
            return result, best_match_name
    except Exception as e:
        print(e)
        return None


def boxer_lookup(boxer):
    """ return info about given boxer (name or global id accepable as param) """
    result, best_match_name = get_request(boxer)
    content = result.content
    soup = BeautifulSoup(content, "lxml")


    profile_table = soup.find_all("table", "rowTable")
    td_values = profile_table[1].find_all("td")
    stripped_td_values = []
    stripped_td_values.append("'name'")
    stripped_td_values.append(best_match_name)
    stripped_td_values.append("'record'")
    profileWLD = soup.find_all("table", "profileWLD")[0]
    record = "%s/%s/%s, %s" %(profileWLD.find_all("td", "bgW")[0].text,
                            profileWLD.find_all("td", "bgL")[0].text,
                            profileWLD.find_all("td", "bgD")[0].text,
                            profileWLD.find_all("th")[0].text)
    stripped_td_values.append(record)
    KOs = int(profileWLD.find_all("th")[0].text.split(" ")[0])
    fights  = int(profileWLD.find_all("td", "bgW")[0].text)+int(profileWLD.find_all("td", "bgL")[0].text)+int(profileWLD.find_all("td", "bgD")[0].text)
    stripped_td_values.append("KO %")
    ko_percent = KOs/fights * 100
    stripped_td_values.append(str(round(ko_percent, 0))+"%")
    for item in td_values:
        text = repr(re.sub(r"(\s+)",r" ",item.text.strip()))
        if (len(text) > 3 and "register as" not in text):
            #print("appending %s" % text)
            stripped_td_values.append(text)
    profile_dict = OrderedDict(itertools.zip_longest(*[iter(stripped_td_values)] * 2, fillvalue=""))

    return profile_dict

def boxer_resume(boxer):
    result, best_match_name = get_request(boxer)
    content = result.content
    soup = BeautifulSoup(content, "lxml")

    #samples = soup.find_all("a", "personLink")
    dataTable = soup.find_all("table", "dataTable")
    tr_values = dataTable[0].find_all("tr", "drawRowBorder")
    fighter_resume = OrderedDict()
    fighter_resume[best_match_name] = "Name"
    for item in tr_values:
        opp_name = item.find_all("a", "personLink")[0].text
        spans = item.find_all("span")
        opp_record = ("%s/%s/%s" % (spans[0].text,spans[1].text,spans[2].text))
        result = item.find_all("div", "boutResult")[0].text
        method = item.find_all("td")[8].text.replace("\n","")
        method = re.sub(" +", " ", method)
        #print("opp: %s, record: %s, result: %s %s" % (opp_name, opp_record, result, method))
        key = "%s (%s)" % (opp_name,opp_record)
        value = "%s %s" % (result, method)
        fighter_resume[key] = value

    return fighter_resume

if __name__ == '__main__':
    dic = boxer_lookup("447121")
    #dic = boxer_resume("terence crawford")
    print(dic)
