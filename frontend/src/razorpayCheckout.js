let pending;
export function loadRazorpay(){
 if(window.Razorpay)return Promise.resolve(window.Razorpay);
 if(pending)return pending;
 pending=new Promise((resolve,reject)=>{
  const script=document.createElement('script');script.src='https://checkout.razorpay.com/v1/checkout.js';script.async=true;
  const fail=()=>{clearTimeout(timer);script.remove();pending=null;reject(new Error('Could not load payment checkout. Please retry.'))};
  const timer=setTimeout(fail,15000);
  script.onerror=fail;script.onload=()=>{if(!window.Razorpay){fail();return}clearTimeout(timer);resolve(window.Razorpay)};
  document.head.appendChild(script);
 });
 return pending;
}
