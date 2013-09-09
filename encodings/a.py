from encodings.aliases import aliases

s='\nos\n'
for x in aliases.keys():
 try:
  a=s.encode(x)
  if a[0]==s[0]and a!=s:
   print(x, a)
 except:
  pass
