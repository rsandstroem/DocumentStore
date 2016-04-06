__author__ = 'aje'


#
# Copyright (c) 2008 - 2013 10gen, Inc. <http://10gen.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

import sys
import re
import datetime
import gridfs
from bson.objectid import ObjectId


# The Document Store Post Data Access Object handles interactions with the Posts collection
class DocStorePostDAO:

    # constructor for the class
    def __init__(self, database):
        self.db = database
        self.fs = gridfs.GridFS(database)

    # returns an array of num_posts posts, reverse ordered
    def get_posts(self, num_posts):

        #cursor = self.posts.find().sort('date', direction=-1).limit(num_posts)
        cursor = self.db.fs.files.find().sort('uploadDate', direction=-1).limit(num_posts)
        l = []
        for post in cursor:
            if 'tags' not in post:
                post.tags = [] # fill it in if its not there already
            if 'comments' not in post:
                post['comments'] = []
            if 'filename' not in post:
                post['filename'] = ''

            l.append({'permalink':post['_id'],
                      'text':post['text'],
                      'title':post['filename'],
                      'tags':post['tags'],
                      'author':post['username'],
                      'comments':post['comments'],
                      'post_date':post['uploadDate'].strftime('%c')})

        return l

    # returns an array of num_posts posts, reverse ordered, filtered by tag
    def get_posts_by_tag(self, tag, num_posts):

        cursor = self.db.fs.files.find({'tags':tag}).sort('uploadDate', direction=-1).limit(num_posts)
        l = []

        for post in cursor:

            if 'tags' not in post:
                post.tags = [] # fill it in if its not there already
            if 'comments' not in post:
                post['comments'] = []
            if 'filename' not in post:
                post['filename'] = ''

            l.append({'permalink':post['_id'],
                      'text':post['text'],
                      'title':post['filename'],
                      'tags':post['tags'],
                      'author':post['username'],
                      'comments':post['comments'],
                      'post_date':post['uploadDate'].strftime('%c')})

        return l

    # returns an array of num_posts posts, reverse ordered, filtered by search text
    def get_posts_by_search(self, search, num_posts):

        cursor = self.db.fs.files.find({"$text": { "$search": search }}).sort('uploadDate', direction=-1).limit(num_posts)
        l = []

        for post in cursor:
            if 'tags' not in post:
                post.tags = [] # fill it in if its not there already
            if 'comments' not in post:
                post['comments'] = []
            if 'filename' not in post:
                post['filename'] = ''

            l.append({'permalink':post['_id'],
                      'text':post['text'],
                      'title':post['filename'],
                      'tags':post['tags'],
                      'author':post['username'],
                      'comments':post['comments'],
                      'post_date':post['uploadDate'].strftime('%c')})

        return l

    # find a post corresponding to a particular permalink
    def get_post_by_permalink(self, permalink):

        post = self.db.fs.files.find_one({'_id': ObjectId(permalink)})
        return post

    # find a binary object corresponding to a particular post
    def get_object_by_post(self, post):

        object = self.fs.get(ObjectId(post['_id']))
        return object

    # add a comment to a particular docstore post
    def add_comment(self, permalink, name, body):

        comment = {'author': name, 'body': body}

        try:
            last_error = self.db.fs.files.update_one({'_id': ObjectId(permalink)}, {'$push': {'comments': comment}}, upsert=False)


            return last_error['n']          # return the number of documents updated

        except:
            print "Could not update the collection, error"
            print "Unexpected error:", sys.exc_info()[0]
            return 0









