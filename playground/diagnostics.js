/* Kasa diagnostics v0.1 — presentation layer, NOT a replacement compiler.
 * Native/JS errors remain authoritative. No automatic source modification.
 * UTF-8 code-point coordinates match the candidate Kasa contract.
 */
(function(root) {
  "use strict";
  const replacements = Object.freeze({ se: "sɛ", mpen: "mpɛn", enye: "ɛnyɛ" });
  const descriptions = Object.freeze({
    SyntaxError: "Kasa could not understand part of this instruction.",
    NameError: "A name was used before Kasa could find its declaration.",
    TypeError: "This operation received a value of the wrong kind.",
    IndexError: "A list position is outside the available items.",
    ZeroDivisionError: "The program tried to divide by zero.",
    ResourceError: "The program reached a safety limit."
  });
  function identifyDeclarations(source) {
    const found = new Set();
    const stripped = source.replace(/"(?:\\.|[^"\\])*"/g, '""');
    for (const line of stripped.split(/\r\n?|\n/)) {
      const part = line.split("#")[0];
      const m = /^\s*ma\s+([\p{L}_][\p{L}\p{N}_]*)\s*(?:=|\[)/u.exec(part);
      if(m) found.add(m[1]);
    }
    return [...found];
  }
  function distanceOne(a,b) {
    const x=[...a],y=[...b];
    if(Math.abs(x.length-y.length)>1)return false;
    let i=0,j=0,diffs=0;
    while(i<x.length && j<y.length) {
      if(x[i]===y[j]) {i++;j++;continue;}
      if(++diffs>1)return false;
      if(x.length>y.length)i++;
      else if(y.length>x.length)j++;
      else {i++;j++;}
    }
    return diffs+(x.length-i)+(y.length-j)===1;
  }
  function diagnose(source,rawError) {
    if (typeof rawError!=="string" || !rawError.trim()) return null;
    const match=/(?:^|\n)([^\n]*?\.kasa):(\d+):(\d+):\s*([A-Za-z]+Error):\s*([^\n]*)/.exec(rawError);
    if(!match)return {code:"KASA-UNKNOWN",category:"RuntimeError",line:null,column:null,title:"Kasa reported an error",explanation:"Read the original engine message below.",suggestion:null,raw:rawError};
    const [,filename,ln,col,category,message]=match;
    const line=Number(ln),column=Number(col);
    const lines=source.replace(/\r\n?/g,"\n").split("\n");
    const current=lines[line-1]||"";
    let code="KASA-"+category.replace(/Error$/,"").toUpperCase();
    let title=category;
    let explanation=descriptions[category]||"Kasa could not complete this instruction.";
    let suggestion=null;
    const first=/^(\s*)([\p{L}_][\p{L}\p{N}_]*)/u.exec(current);
    if(category==="SyntaxError" && first && Object.hasOwn(replacements,first[2])) {
      const expected=replacements[first[2]];
      // Only suggest an alternative when the actual compiler reported a syntax error.
      code="KASA-KW001";title="Possible Kasa keyword spelling";
      explanation="The first word on this line resembles a Kasa keyword. Kasa keywords use their exact Unicode spelling.";
      suggestion="Try '"+expected+"' instead of '"+first[2]+"'. The special-letter toolbar can insert it.";
    } else if(category==="SyntaxError" && /Expected 'a' after the condition/.test(message)){
      code="KASA-SYN002";title="Missing conditional marker";
      explanation="A Kasa sɛ condition ends with the marker 'a' before its body.";
      suggestion="Write: sɛ CONDITION a — then add the body and close with awiei.";
    } else if(category==="SyntaxError" && /Unterminated string/.test(message)){
      code="KASA-SYN003";title="Text is missing a closing quote";
      explanation="A text value begins and ends with a double quotation mark.";
      suggestion='Close the string with a matching double quote (").';
    } else if(category==="NameError" && /Unknown name '([^']+)'/.test(message)){
      const missing=/Unknown name '([^']+)'/.exec(message)[1];
      code="KASA-NAME001";title="Unknown variable or function name";
      const candidates=identifyDeclarations(source).filter(name=>distanceOne(name,missing));
      explanation="Kasa could not find '"+missing+"'. Names are case-sensitive and must be spelled consistently.";
      suggestion=candidates.length===1?"Did you mean '"+candidates[0]+"'? Check the declaration before using it.":"Check that '"+missing+"' was declared with ma, or defined as a function, before use.";
    } else if(category==="ZeroDivisionError"){
      code="KASA-MATH001";title="Division by zero";
      explanation="Division by zero is undefined; a denominator cannot equal 0.";
      suggestion="Check the denominator before dividing, especially when it comes from user input.";
    } else if(category==="IndexError"){
      code="KASA-LIST001";title="List index outside its range";
      explanation="List positions begin at 0. A list of length 3 has indexes 0, 1 and 2.";
      suggestion="Use tentɛn(list_name) to inspect the length, then select a valid index.";
    } else if(category==="TypeError" && /Condition must/.test(message)){
      code="KASA-TYPE001";title="A condition must be true or false";
      explanation="Kasa conditions require nokware or atoro, not arbitrary numbers or text.";
      suggestion="Use a comparison such as sɛ mfe >= 18 a instead of testing the number by itself.";
    }
    const excerpt=current ? current : null;
    return {code,category,line,column,title,explanation,suggestion,excerpt,filename:filename.trim(),raw:rawError};
  }
  root.KasaDiagnostics=Object.freeze({diagnose});
  if(typeof module!=="undefined"&&module.exports)module.exports=root.KasaDiagnostics;
})(typeof self!=="undefined"?self:globalThis);
