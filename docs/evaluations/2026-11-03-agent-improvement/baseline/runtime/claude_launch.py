"""Launch Claude Code against the local guarded API without changing the user's normal setup."""
import argparse,json,os,pathlib,shutil,subprocess,sys
from bonsai_ensure import ensure
ROOT=pathlib.Path(__file__).resolve().parent
TOOLS='Read,Write,Edit,Bash,Glob,Grep'

def environment(profile):
 settings=json.loads((ROOT/'profiles.json').read_text(encoding='utf-8'))[profile]
 env=os.environ.copy()
 for name in ('ANTHROPIC_API_KEY','ANTHROPIC_CUSTOM_HEADERS','CLAUDE_CODE_OAUTH_TOKEN','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY','DISABLE_COMPACT'):
  env.pop(name,None)
 context=settings['context'];reserve=24576 if profile.startswith('dflash') else 32768
 env.update(ANTHROPIC_BASE_URL='http://127.0.0.1:8081',ANTHROPIC_AUTH_TOKEN='local',ANTHROPIC_MODEL='bonsai2-27b',CLAUDE_CONFIG_DIR=str(ROOT/'claude-home'),CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',CLAUDE_CODE_MAX_CONTEXT_TOKENS=str(context),CLAUDE_CODE_AUTO_COMPACT_WINDOW=str(context-reserve),CLAUDE_CODE_MAX_OUTPUT_TOKENS='16384',API_TIMEOUT_MS='900000')
 for slot in ('OPUS','SONNET','HAIKU','FABLE'):env['ANTHROPIC_DEFAULT_'+slot+'_MODEL']='bonsai2-27b'
 hosts=[v for v in env.get('NO_PROXY','').split(',') if v]+['127.0.0.1','localhost']
 env['NO_PROXY']=','.join(dict.fromkeys(hosts))
 return env

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=('dflash144','base256','dflash128graph'),default='dflash144');parser.add_argument('--project',type=pathlib.Path,default=pathlib.Path.cwd());parser.add_argument('claude_args',nargs=argparse.REMAINDER);args=parser.parse_args()
 executable=shutil.which('claude')
 if not executable:raise RuntimeError('Claude Code CLI is not installed or is not on PATH')
 project=args.project.resolve()
 if not project.is_dir():raise RuntimeError('Project directory does not exist: '+str(project))
 ensure(args.profile);env=environment(args.profile);(ROOT/'claude-home').mkdir(exist_ok=True)
 extra=args.claude_args[1:] if args.claude_args[:1]==['--'] else args.claude_args
 cmd=[executable,'--bare','--setting-sources','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--model','bonsai2-27b','--tools',TOOLS]+extra
 p=subprocess.Popen(cmd,cwd=project,env=env)
 while True:
  try:return p.wait()
  except KeyboardInterrupt:continue # The interactive child handles Ctrl+C itself.
if __name__=='__main__':sys.exit(main())
