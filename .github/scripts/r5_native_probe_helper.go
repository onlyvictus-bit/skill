// Probe-only helper: compile INSIDE the exact pinned Beads module.
package main

import (
 "context"
 "encoding/json"
 "fmt"
 "os"
 "path/filepath"
 "regexp"
 "time"
 "github.com/steveyegge/beads/internal/storage/embeddeddolt"
)
func main() { if err:=run();err!=nil {fmt.Fprintln(os.Stderr,err);os.Exit(2)} }
func run() error {
 if len(os.Args)!=8 {return fmt.Errorf("expected root, database, project, branch, operation, issue-or-new-branch, title")}
 root,db,project,branch,op,id,title:=os.Args[1],os.Args[2],os.Args[3],os.Args[4],os.Args[5],os.Args[6],os.Args[7]
 if !filepath.IsAbs(root) {return fmt.Errorf("absolute disposable root required")}
 marker,err:=os.ReadFile(filepath.Join(root,"r5-disposable-probe.json"));if err!=nil{return err}
 var identity map[string]string;if err=json.Unmarshal(marker,&identity);err!=nil{return err}
 if identity["root"]!=root || identity["database"]!=db || identity["project"]!=project {return fmt.Errorf("disposable identity mismatch")}
 for _,p:=range []string{root,filepath.Join(root,".beads"),filepath.Join(root,".beads","metadata.json")} {s,e:=os.Lstat(p);if e!=nil{return e};if s.Mode()&os.ModeSymlink!=0{return fmt.Errorf("symlink refused")}}
 meta,err:=os.ReadFile(filepath.Join(root,".beads","metadata.json"));if err!=nil{return err};var m map[string]interface{};if err=json.Unmarshal(meta,&m);err!=nil{return err}
 if m["project_id"]!=project || m["dolt_database"]!=db || m["backend"]!="dolt" || m["dolt_mode"]!="embedded" {return fmt.Errorf("metadata mismatch")}
 if branch!="main" && !regexp.MustCompile(`^r5probe[a-z]+$`).MatchString(branch) {return fmt.Errorf("branch refused")}
 if op!="read" && op!="fork" && op!="write" {return fmt.Errorf("operation refused")}
 if op=="fork" && (branch!="main" || !regexp.MustCompile(`^r5probe[a-z]+$`).MatchString(id)) {return fmt.Errorf("fork refused")}
 if op=="write" && (branch=="main" || len(title)==0) {return fmt.Errorf("only source-branch title write permitted")}
 ctx,cancel:=context.WithTimeout(context.Background(),30*time.Second);defer cancel()
 var s *embeddeddolt.EmbeddedDoltStore
 if op=="read" {s,err=embeddeddolt.OpenReadOnly(ctx,filepath.Join(root,".beads"),db,branch)} else {s,err=embeddeddolt.Open(ctx,filepath.Join(root,".beads"),db,branch)}
 if err!=nil{return err};defer s.Close()
 before,err:=s.GetCurrentCommit(ctx);if err!=nil{return err}
 selected,err:=s.CurrentBranch(ctx);if err!=nil{return err};if selected!=branch{return fmt.Errorf("selected branch mismatch: %s",selected)}
 if op=="fork" {err=s.Branch(ctx,id)}
 if op=="write" {err=s.UpdateIssue(ctx,id,map[string]interface{}{"title":title},"r5branchprobe");if err==nil {_,err=s.CommitAll(ctx,"R5 disposable source branch probe")}}
 if err!=nil{return err}
 after,err:=s.GetCurrentCommit(ctx);if err!=nil{return err}
 out:=map[string]interface{}{"branch":selected,"before_head":before,"head":after,"operation":op}
 if op!="fork" {issue,e:=s.GetIssue(ctx,id);if e!=nil{return e};out["issue"]=issue;log,e:=s.Log(ctx,0);if e!=nil{return e};out["log"]=log;conflicts,e:=s.GetConflicts(ctx);if e!=nil{return e};out["conflicts"]=conflicts}
 return json.NewEncoder(os.Stdout).Encode(out)
}
