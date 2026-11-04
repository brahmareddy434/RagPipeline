"""Build the standalone HTML guides and a local course index."""
import html
import json
from pathlib import Path
from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parent
CSS="""body{margin:0;color:#192638;background:#f2f5f9;font:17px/1.7 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:880px;margin:32px auto;padding:40px 54px;background:white;border:1px solid #dbe2eb;border-radius:10px}
h1{font-size:36px;line-height:1.2;margin:18px 0 30px}h2{font-size:25px;margin-top:40px;line-height:1.3}h3{font-size:20px;margin-top:26px}
a{color:#164e9d}nav{font-size:15px;border-bottom:1px solid #ddd;padding-bottom:16px}pre{background:#f4f6f8;padding:18px;overflow:auto;font-size:14px;line-height:1.5}
code{font-family:Consolas,monospace}table{border-collapse:collapse;width:100%;font-size:15px;margin:22px 0}
td,th{border:1px solid #d5dce6;padding:10px;text-align:left;vertical-align:top}th{background:#eaf0f8}
blockquote{margin-left:0;padding-left:18px;border-left:3px solid #cad5e4;color:#46576b}li{margin:7px 0}
@media(max-width:700px){main{margin:0;padding:24px;border:0;border-radius:0}h1{font-size:29px}table{font-size:13px}}
@media print{body{background:white;font-size:11pt}main{border:0;padding:0;margin:0;max-width:none}nav{display:none}h2,h3{break-after:avoid}pre{white-space:pre-wrap;overflow-wrap:anywhere}tr{break-inside:avoid}a{color:inherit}}
"""
parser=MarkdownIt("commonmark",{"html":False}).enable("table")
pages=[]
for path in sorted((ROOT/"guides").glob("0*.md")):
    source=path.read_text(encoding="utf-8")
    title=source.splitlines()[0].lstrip("# ")
    target=path.with_suffix(".html")
    body=parser.render(source)
    target.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+
        html.escape(title)+'</title><style>'+CSS+'</style><main><nav><a href="../index.html">All weeks</a> · <a href="'+path.name+'">Markdown source</a></nav>'+
        body+'</main></html>',encoding="utf-8")
    pages.append({"title":title,"html":"guides/"+target.name,"markdown":"guides/"+path.name,"words":len(source.split())})
items="".join('<li><a href="'+p["html"]+'">'+html.escape(p["title"])+'</a> <small>('+str(p["words"])+' words)</small></li>' for p in pages)
intro="""<h1>Your seven week AI engineering course</h1><p>Learn the ideas, inspect the code, run the experiments, and understand the evidence.
Week 1 is theory only. Weeks 2 to 6 build and evaluate a local HR document assistant, and Week 7 turns it into an agent and measures whether that was worth it.</p>
<p>Read <a href="README.md">the quick start</a>, <a href="COVERAGE.md">the topic coverage map</a>,
and the per-week KT documents under <code>docs/</code> for tested results and limitations.</p>"""
(ROOT/"index.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Seven week AI engineering course</title><style>'+CSS+'</style><main>'+intro+'<ol>'+items+'</ol><p>Use your browser Print command for a paper or PDF copy. Each guide has a print layout.</p></main></html>',encoding="utf-8")
(ROOT/"guide_manifest.json").write_text(json.dumps(pages,indent=2),encoding="utf-8")
print(json.dumps(pages,indent=2))
