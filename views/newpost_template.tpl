<!doctype HTML>
<html>
<head>
<title>Create a new post</title>
</head>
<body>
%if (username != None):
Welcome {{username}}        <a href="/logout">Logout</a> | <a href="/">Blog Home</a><p>
%end
<form action="/newpost" method="POST" enctype="multipart/form-data">
{{errors}}
<h2>New file name</h2>
Short but descriptive, please.<br>
<input type="text" name="subject" size="120" value="{{subject}}"><br>
<h2>File<h2>
<input type="file" name="data" /><br>
<h2>Tags</h2>
Comma separated, please.<br>
<input type="text" name="tags" size="120" value="{{tags}}"><br>
<p>
<input type="submit" value="Submit">

</body>
</html>

