# doing necessary imports

from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)  # initialising the flask app with the name 'app'


# route with allowed methods as POST and GET
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        # obtaining the search string entered in the form
        searchString = request.form['content'].replace(" ", "")
        try:
            # opening a connection to Mongo
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
            # connecting to the database called crawlerDB
            db = dbConn['crawlerDB']
            # searching the collection with the name same as the keyword
            reviews = db[searchString].find({})
            if reviews.count() > 0:  # if there is a collection with searched keyword and it has records in it
                # show the results to user
                return render_template('results.html', reviews=reviews)
            else:
                # preparing the URL to search the product on flipkart
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString
                # requesting the webpage from the internet
                uClient = uReq(flipkart_url)
                flipkartPage = uClient.read()  # reading the webpage
                uClient.close()  # closing the connection to the web server
                # parsing the webpage as HTML
                flipkart_html = bs(flipkartPage, "html.parser")
                # seacrhing for appropriate tag to redirect to the product link
                bigboxes = flipkart_html.findAll(
                    "div", {"class": "bhgxx2 col-12-12"})
                # the first 3 members of the list do not contain relevant information, therefore deleting them.
                del bigboxes[0:3]
                box = bigboxes[0]  # taking the first iteration (for demo)
                productLink = "https://www.flipkart.com" + \
                    box.div.div.div.a['href']  # extracting the actual product link
                # getting the product page from server
                prodRes = requests.get(productLink)
                # parsing the product page as HTML
                prod_html = bs(prodRes.text, "html.parser")
                # finding the HTML section containing the customer comments
                commentboxes = prod_html.find_all('div', {'class': "_3nrCtb"})

                # creating a collection with the same name as search string. Tables and Collections are analogous.
                table = db[searchString]
                reviews = []  # initializing an empty list for reviews
                #  iterating over the comment section to get the details of customer and their comments
                for commentbox in commentboxes:
                    try:
                        name = commentbox.div.div.find_all(
                            'p', {'class': '_3LYOAd _3sxSiS'})[0].text

                    except:
                        name = 'No Name'

                    try:
                        rating = commentbox.div.div.div.div.text

                    except:
                        rating = 'No Rating'

                    try:
                        commentHead = commentbox.div.div.div.p.text
                    except:
                        commentHead = 'No Comment Heading'
                    try:
                        comtag = commentbox.div.div.find_all(
                            'div', {'class': ''})
                        custComment = comtag[0].div.text
                    except:
                        custComment = 'No Customer Comment'
                    mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                              "Comment": custComment}  # saving that detail to a dictionary
                    # insertig the dictionary containing the rview comments to the collection
                    x = table.insert_one(mydict)
                    # appending the comments to the review list
                    reviews.append(mydict)
                # showing the review to the user
                return render_template('results.html', reviews=reviews)
        except:
            return 'something is wrong'
            # return render_template('results.html')
    else:
        return render_template('index.html')


if __name__ == "__main__":
    # running the app on the local machine on port 8000
    app.run(port=8000, debug=True)
