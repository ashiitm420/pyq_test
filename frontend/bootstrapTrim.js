import {PurgeCSS} from 'purgecss';

// Trim only Bootstrap. App styles and KaTeX's generated markup are untouched.
export function bootstrapTrim(){
 return {name:'trim-bootstrap',enforce:'pre',apply:'build',async transform(code,id){
  if(!id.replaceAll('\\','/').endsWith('/bootstrap/dist/css/bootstrap.min.css'))return;
  const [result]=await new PurgeCSS().purge({
   content:['index.html','src/**/*.{vue,js}','../backend/templates/**/*.html'],
   css:[{raw:code}],
   safelist:{standard:[/^(?:btn|alert|form|table|badge|spinner|text-bg|bg|border)-/,/^(?:show|active|disabled|collapse|collapsing|fade|was-validated|is-valid|is-invalid)$/,/^(?:row|col)(?:-|$)/]},
   fontFace:false,keyframes:false,variables:false,
  });
  return {code:result.css,map:null};
 }};
}
