// Immutable, allowlisted recall over actual AtomSpace links/Values. No evaluator.
#include <opencog/atomspace/AtomSpace.h>
#include <opencog/atoms/base/Node.h>
#include <opencog/atoms/base/Link.h>
#include <opencog/atoms/value/FloatValue.h>
#include <opencog/atoms/value/StringValue.h>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <algorithm>
using namespace opencog;
static std::string hex(const std::string& s) {
    if(s.empty()) return "-";
    std::string r; const char* d="0123456789abcdef";
    for(unsigned char c:s){r+=d[c>>4];r+=d[c&15];} return r;
}
static std::string unhex(const std::string& s) {
    if(s=="-")return "";
    if(s.empty()||s.size()%2||s.size()>131072)throw std::runtime_error("hex bound");
    auto d=[](char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("hex digit");};
    std::string r;for(size_t i=0;i<s.size();i+=2)r+=char(16*d(s[i])+d(s[i+1]));return r;
}
template<class T> static T take(std::istringstream& in){T v;if(!(in>>v))throw std::runtime_error("missing field");return v;}
static void end(std::istringstream& in){std::string x;if(in>>x)throw std::runtime_error("trailing fields");}
static size_t number(std::istringstream& in,size_t cap){auto s=take<std::string>(in);if(s.empty()||s.size()>9||s.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("integer syntax");auto n=std::stoull(s);if(n>cap)throw std::runtime_error("integer bound");return n;}
static bool prefix(const std::string&s,const std::string&p){return s.rfind(p,0)==0;}
static std::string name(const Handle& h){if(!h||h->get_type()!=CONCEPT_NODE)throw std::runtime_error("expected ConceptNode");return h->get_name();}
static const HandleSeq& outgoing(const Handle& h){if(!h||h->get_type()!=LIST_LINK)throw std::runtime_error("expected ordered ListLink");return LinkCast(h)->getOutgoingSet();}
static std::string role(const Handle& h){if(!h||h->get_type()!=PREDICATE_NODE)return "";return h->get_name();}
static void literal(const Handle& h){auto& o=outgoing(h);if(o.size()!=4||role(o[0])!="recall:literal/v1"||(name(o[1])!="polarity:+"&&name(o[1])!="polarity:-")||!prefix(name(o[2]),"symbol:"))throw std::runtime_error("literal shape");auto&a=outgoing(o[3]);if(a.empty()||role(a[0])!="recall:arguments/v1")throw std::runtime_error("argument shape");for(size_t i=1;i<a.size();++i)if(!prefix(name(a[i]),"symbol:"))throw std::runtime_error("argument type");}
int main(){
 try{
    AtomSpace space;std::vector<Handle> refs;std::map<Handle,size_t> canonical;
    std::map<std::pair<Handle,Handle>,char> values;std::map<std::string,Handle> records;
    size_t bytes=0,commands=0,relations=0,queries=0;bool sealed=false;std::string view,line;
    std::cout<<"native-atomspace-recall/v1 "<<ATOMSPACE_PIN<<'\n'<<std::flush;
    auto node=[&](const std::string& n,Type t=CONCEPT_NODE){return space.get_node(t,std::string(n));};
    auto val=[&](Handle h,const std::string& k){auto key=node(k,PREDICATE_NODE);if(!key)throw std::runtime_error("missing Value key");auto v=h->getValue(key);if(!v||v->get_type()!=STRING_VALUE)throw std::runtime_error("missing StringValue");return StringValueCast(v)->value().at(0);};
    auto checkrecord=[&](Handle h){auto n=name(h);if(!prefix(n,"record:")||!records.count(n.substr(7))||records.at(n.substr(7))!=h)throw std::runtime_error("unregistered record");};
    auto bounded_line=[&](){line.clear();char c;while(std::cin.get(c)){if(c=='\n')return true;if(line.size()>=262144||c=='\0'||c=='\r')throw std::runtime_error("line bound/encoding");line+=c;}return !line.empty();};
    while(bounded_line()){
      if(line.size()>262144)throw std::runtime_error("line bound");
      std::istringstream in(line);auto op=take<std::string>(in);
      if(!sealed){
        bytes+=line.size()+1;if(++commands>100000||bytes>8388608)throw std::runtime_error("load bound");
        if(op=="N"||op=="P"||op=="L"){
          Handle atom;
          if(op!="L")atom=space.add_node(op=="N"?CONCEPT_NODE:PREDICATE_NODE,unhex(take<std::string>(in)));
          else {size_t count=number(in,4096);HandleSeq out;for(size_t i=0;i<count;++i)out.push_back(refs.at(number(in,100000)));atom=space.add_link(LIST_LINK,std::move(out));}
          end(in);canonical.emplace(atom,refs.size());refs.push_back(atom);
        }else if(op=="S"||op=="F"){
          auto a=refs.at(number(in,100000)),k=refs.at(number(in,100000));
          if(k->get_type()!=PREDICATE_NODE)throw std::runtime_error("Value key type");
          if(values.count({a,k}))throw std::runtime_error("duplicate Value in immutable load");
          if(op=="S")space.set_value(a,k,std::make_shared<StringValue>(unhex(take<std::string>(in))));
          else{size_t count=number(in,4096);std::vector<double> v;for(size_t i=0;i<count;++i){double x=take<double>(in);if(!std::isfinite(x))throw std::runtime_error("nonfinite Value");v.push_back(x);}space.set_value(a,k,std::make_shared<FloatValue>(v));}
          end(in);values[{a,k}]=op[0];
        }else if(op=="R"){
          auto id=unhex(take<std::string>(in));auto h=refs.at(number(in,100000));end(in);
          if(records.size()>=512||name(h)!="record:"+id||!records.emplace(id,h).second)throw std::runtime_error("duplicate/conflicting record identity");
        }else if(op=="T"){
          view=unhex(take<std::string>(in));auto nr=number(in,100000),nv=number(in,100000),ns=number(in,512),ne=number(in,1024);end(in);
          if(view.empty()||nr!=refs.size()||nv!=values.size()||ns!=records.size())throw std::runtime_error("partial load");
          for(auto& entry:canonical){auto h=entry.first;if(h->get_type()!=LIST_LINK)continue;auto&o=outgoing(h);if(o.empty())continue;auto tag=role(o[0]);
            if(tag=="recall:literal/v1"){literal(h);continue;}
            if(tag=="recall:arguments/v1"||tag=="recall:premises/v1"||tag=="recall:model-supports/v1")continue;
            if(!prefix(tag,"recall:"))continue;
            bool producer=tag=="recall:producer/v1",support=tag=="recall:current/v1"||tag=="recall:historical/v1"||tag=="recall:report/v1";
            bool probe=tag=="recall:probe/v1",model=tag=="recall:model/v1";
            size_t arity=producer||model?5:probe?6:support?4:0;
            if(!arity||o.size()!=arity||!prefix(name(o[1]),"context:"))throw std::runtime_error("relation shape");
            if(producer||support){literal(o[2]);checkrecord(o[3]);}
            if(producer){auto&p=outgoing(o[4]);if(p.size()!=6||role(p[0])!="recall:premises/v1")throw std::runtime_error("five ordered premises required");for(size_t j=1;j<p.size();++j)literal(p[j]);}
            if(probe){auto t=name(o[2]);if(t=="symbol:numeric")literal(o[3]);else if((t!="symbol:product"&&t!="symbol:health")||!prefix(name(o[3]),"symbol:"))throw std::runtime_error("probe target type");checkrecord(o[4]);auto n=name(o[5]);if(!prefix(n,"integer:")||n.size()==8||n.substr(8).find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("exact opportunity required");}
            if(model){checkrecord(o[2]);auto&p=outgoing(o[3]);if(p.size()!=3||role(p[0])!="recall:model-supports/v1")throw std::runtime_error("model support shape");for(size_t j=1;j<p.size();++j)if(!prefix(name(p[j]),"record:"))throw std::runtime_error("model premise identity");if(name(o[4])!="bool:true"&&name(o[4])!="bool:false")throw std::runtime_error("model revoked flag");}
            auto record=o[model?2:probe?4:3];
            auto expected_kind=producer?"rule":probe?"probe":model?"model":tag=="recall:report/v1"?"report":"support";
            if(val(record,"source:kind/v1")!=expected_kind)throw std::runtime_error("relation/source kind mismatch");
            ++relations;
          }
          if(relations!=ne)throw std::runtime_error("incomplete relation load");
          for(auto&r:records){val(r.second,"source:payload/v1");val(r.second,"source:kind/v1");}
          // Full independent structural/Value readback before any queryable view.
          std::cout<<std::setprecision(17);
          for(size_t i=0;i<refs.size();++i){auto a=space.get_atom(refs[i]);std::cout<<"A "<<i<<' '<<canonical.at(a)<<' ';
            if(a->get_type()==LIST_LINK){auto&o=outgoing(a);std::cout<<"L "<<o.size();for(auto& h:o)std::cout<<' '<<canonical.at(h);}
            else std::cout<<(a->get_type()==CONCEPT_NODE?"N ":"P ")<<hex(a->get_name());std::cout<<'\n';}
          for(auto&e:values){auto v=e.first.first->getValue(e.first.second);std::cout<<e.second<<' '<<canonical.at(e.first.first)<<' '<<canonical.at(e.first.second);
            if(e.second=='S')std::cout<<' '<<hex(StringValueCast(v)->value().at(0));else{auto&d=FloatValueCast(v)->value();std::cout<<' '<<d.size();for(auto x:d)std::cout<<' '<<x;}std::cout<<'\n';}
          std::cout<<"READY "<<hex(view)<<' '<<space.get_size()<<' '<<relations<<' '<<records.size()<<' '<<values.size()<<'\n'<<std::flush;sealed=true;
        }else throw std::runtime_error("unknown load command");
        continue;
      }
      if(op=="CLOSE"){end(in);std::cout<<"CLOSED\n"<<std::flush;return 0;}
      if(op!="Q")throw std::runtime_error("sealed view is immutable");
      if(++queries>4096)throw std::runtime_error("view query bound");
      auto nonce=take<std::string>(in),binding=unhex(take<std::string>(in)),kind=take<std::string>(in);
      auto visit_limit=number(in,4096),result_limit=number(in,512);
      if(nonce.size()>32||binding!=view)throw std::runtime_error("stale view request");
      if(kind=="record"){
        auto id=unhex(take<std::string>(in));end(in);auto h=node("record:"+id);
        if(!h||!records.count(id)){std::cout<<"QRESULT "<<nonce<<" COMPLETE COMPLETE 0 0\nEND "<<nonce<<'\n'<<std::flush;continue;}
        if(!visit_limit||!result_limit){std::cout<<"QRESULT "<<nonce<<" INCOMPLETE "<<(!visit_limit?"VISIT_BOUND":"RESULT_BOUND")<<" 0 0\nEND "<<nonce<<'\n'<<std::flush;continue;}
        std::cout<<"QRESULT "<<nonce<<" COMPLETE COMPLETE 1 1\nD "<<hex(id)<<' '<<hex(val(h,"source:payload/v1"))<<"\nEND "<<nonce<<'\n'<<std::flush;continue;
      }
      std::map<std::string,std::string> tags={{"producers","producer"},{"current","current"},{"historical","historical"},{"reports","report"},{"probes","probe"},{"models","model"},{"all_rules","producer"},{"all_current","current"}};
      if(!tags.count(kind))throw std::runtime_error("unknown query kind");
      auto ctx=node("context:"+unhex(take<std::string>(in)));Handle target;std::string report_type;
      auto readliteral=[&](){auto pol=take<std::string>(in);if(pol!="+"&&pol!="-")throw std::runtime_error("polarity");auto pred=node("symbol:"+unhex(take<std::string>(in)));auto n=number(in,4095);HandleSeq args;auto at=node("recall:arguments/v1",PREDICATE_NODE);bool exists=bool(at)&&bool(pred);args.push_back(at);for(size_t i=0;i<n;++i){auto a=node("symbol:"+unhex(take<std::string>(in)));exists=exists&&bool(a);args.push_back(a);}auto lt=node("recall:literal/v1",PREDICATE_NODE),ph=node("polarity:"+pol);if(!exists||!lt||!ph)return Handle();auto ah=space.get_link(LIST_LINK,std::move(args));if(!ah)return Handle();return space.get_link(LIST_LINK,{lt,ph,pred,ah});};
      bool all=kind=="models"||kind=="all_rules"||kind=="all_current";
      if(kind=="probes"){report_type=take<std::string>(in);if(report_type=="numeric")target=readliteral();else if(report_type=="product"||report_type=="health")target=node("symbol:"+unhex(take<std::string>(in)));else throw std::runtime_error("probe query type");}
      else if(!all)target=readliteral();end(in);
      Handle anchor=all?ctx:target;size_t visits=0;std::string reason="COMPLETE";
      std::vector<std::pair<std::string,Handle>> found;
      if(ctx&&anchor){
        // Check native incoming cardinality before materializing its copy.
        auto size=anchor->getIncomingSetSizeByType(LIST_LINK,&space);
        if(size>visit_limit)reason="VISIT_BOUND";
        else{auto incoming=anchor->getIncomingSetByType(LIST_LINK,&space);
          for(auto& h:incoming){++visits;auto&o=outgoing(h);if(o.size()<2||role(o[0])!="recall:"+tags.at(kind)+"/v1"||o[1]!=ctx)continue;
            if(!all){if(kind=="probes"){if(name(o[2])!="symbol:"+report_type||o[3]!=target)continue;}else if(o[2]!=target)continue;}
            auto record=o[kind=="models"?2:kind=="probes"?4:3];checkrecord(record);found.emplace_back(name(record).substr(7),h);
            if(found.size()>result_limit){reason="RESULT_BOUND";found.clear();break;}
          }
        }
      }
      std::sort(found.begin(),found.end(),[](auto&a,auto&b){return a.first<b.first;});
      std::cout<<"QRESULT "<<nonce<<' '<<(reason=="COMPLETE"?"COMPLETE":"INCOMPLETE")<<' '<<reason<<' '<<visits<<' '<<found.size()<<'\n';
      for(auto& result:found){auto&o=outgoing(result.second);std::vector<Handle> details;
        if(kind=="producers"||kind=="all_rules"){auto&p=outgoing(o[4]);details.assign(p.begin()+1,p.end());}
        if(kind=="models"){auto&p=outgoing(o[3]);details.assign(p.begin()+1,p.end());}
        if(kind=="probes")details.push_back(o[5]);
        std::cout<<"I "<<hex(result.first)<<' '<<details.size();for(auto& h:details)std::cout<<' '<<canonical.at(h);std::cout<<'\n';}
      std::cout<<"END "<<nonce<<'\n'<<std::flush;
    }
    if(!sealed)throw std::runtime_error("partial load without seal");
 }catch(const std::exception&e){std::cerr<<"Native recall rejected: "<<e.what()<<'\n';return 1;}
}
