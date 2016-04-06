<!doctype HTML>
<html
<head>
<title>
Document Store Post
</title>
</head>
<body>
%if (username != None):
Welcome {{username}}        <a href="/logout">Logout</a> |
%end
<a href="/">Document Store Home</a><br><br>

<h2>{{post['filename']}}</h2>
Posted {{post['uploadDate'].strftime('%c')}}<i> By {{post['username']}}</i><br>
<hr>
<h3>Extracted text</h3>
{{!post['text']}}
<h3>Original document</h3>
<a href='{{objectpath}}'>Original</a>
<p>
<em>Filed Under</em>:
%if ('tags' in post):
%for tag in post['tags'][0:1]:
<a href="/tag/{{tag}}">{{tag}}</a>
%for tag in post['tags'][1:]:
, <a href="/tag/{{tag}}">{{tag}}</a>
%end
%end
%end
<p>
Comments:
<ul>
%if ('comments' in post):
%numComments = len(post['comments'])
%else:
%numComments = 0
%end
%for i in range(0, numComments):
Author: {{post['comments'][i]['author']}}<br>
{{post['comments'][i]['body']}}<br>
<hr>
%end
<h3>Add a comment</h3>
<form action="/newcomment" method="POST">
<input type="hidden" name="permalink", value="{{post['_id']}}">
{{errors}}
<b>Comment</b><br>
<textarea name="commentBody" cols="60" rows="10">{{comment['body']}}</textarea><br>
<input type="submit" value="Submit">
</ul>
</body>
</html>


