# -*- coding: utf-8 -*-

email_conf = '''
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interest Accepted</title>
    <link rel="stylesheet" href="global.css">

<style>
  * {
  margin: 0;
}

body {
 max-width: 550px;
  margin: auto;
  font-family: Satoshi, sans-serif;;
}

#khushi {
  display: flex;
  background-color: #DEA500;
  text-align: center;
  align-items: center;
  color: white;
  justify-content: center;


}

#khushi>div>img {
  margin: 10px;
  border-radius: 10px;
  width: 70px;
  height: 70px;
}

#khushi>div:nth-child(2) {
  text-align: left;

}

#khushi>div:nth-child(2)>h1 {
  font-size: 20px;
  text-transform: uppercase;

}

#khushi>div:nth-child(2)>p {
  font-size: 10px;

}

h4 {
  margin: 0;

}

#banner {
  height: 200px;

}

#banner>img {
  max-width: 600px;
  width: 100%;

}

#rohan>p {
  margin: 20px 0px;
  margin-left: 15px;
  font-size: 18px;
}

#rohan>h1 {
  margin: 6px 0px;
  margin-left: 15px;

}

#rohan>div {
  border: 0.5px solid rgba(128, 128, 128, 0.332);
  border-radius: 15px;
  margin: 10px;
  padding: 0px;
}

#rohan>div>div {
  display: flex;
  align-items: center;


}

#rohan>div>div>div>img {
  border-radius: 15px;
  margin-right: 10px;
  margin: 15px;

}

#rohan>div>div>div>div {
  margin: 15px;
  font-size: 15px;


}

#rohan>div>div>div>div:nth-child(2) {
  font-weight: bolder;
  font-size: 25px;
}

.about {
  font-size: 15px;
  margin: 10px 0;
  font-weight: 500;
  margin: 15px;
}

.jaipur {
  font-size: 18px;
  margin: 15px;
}

#pagalu {
  border-radius: 0 0 15px;
  background-color: rgba(255, 192, 203, 0.36);
  margin: 0px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

#pagalu>div>img {
  height: 70px;
  width: 70px;
}

#chudale {
  font-weight: bolder;
  font-size: 20px;
}

#mota {
  font-size: 20px;
}

#tati p {
  margin-top: 50px;
  text-align: center;
  font-size:20px ;

}
#tati>div:nth-child(2){
display: flex;
justify-content: center;
 }

#tati>div>button{
width: 190px;
  height: 50px;
margin: 40px 0;
  text-align: center;
  font-size: 25px;
  border-radius: 10px;
  background-color:#F6404F;
  color:blanchedalmond;
  border: none;

}
#moto2 h5{
  text-align: center;
}
#moto2>div:nth-child(2){
display: flex;
justify-content: center;
}

.ruhi{ 
  display: flex;
  justify-content: center;
  margin: 20px;
  width: 150px;
  height: 50px;
  
}
#lorem{
  margin:50px 0px 5px 15px
}


#dolor{
text-align: center;
  font-size:15px ;
  margin-top: 0px;
}
#dolor a{
  text-underline-position: above;
  color: #F6404F;
}
.elit{
  font-size:12px ;
  margin:0 15px;
  color:rgb(92, 90, 90)
    
  }
.elit>a{
  text-decoration: underline rgb(95, 173, 204);
  color: rgb(65, 149, 182);
}
#moto2 h1{
  font-size: 17px;
  font-weight:lighter;
}
#you{
text-align: center;
 margin-top:15px;

 font-size: 13px;
}
#you a{
  text-decoration-line: underline;
  color: #F6404F;
}
#you span{
  text-decoration-line: underline;
  color: #F6404F;
}

#type{
  display: flex;
  justify-content: center;
}
  
 #type img{
 margin: 10px;
 border-radius: 10px;
 padding: autopx;
 align-items: center;
 display:inline-flex ;
 text-align: center;
 align-items: center;

 justify-content: center;

 }
 #dolor>span{
  color:#F6404F;
 }

#akash {
  background-color: aliceblue;
  width: 550px;
  border: grey solid;
  border-radius: 4px;
}

</style>
</head>
<body style="max-width: 600px; margin: auto; font-family: Satoshi, sans-serif;">
  <div>
    <table  style="background: #DEA500;color:white;height:100px"cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr>
            <td  style=" padding-left:24%" valign="middle" style="padding: 10px;">
                <img style="border-radius: 10px; width: 70px; height: 70px;" src="https://dev-medico.s3.ap-south-1.amazonaws.com/heartimage3.png" alt="">
            </td>
            <td   style=" padding-left:8%"  valign="middle" style="padding: 10px;">
                <h1 style="font-size: 20px; text-transform: uppercase; margin: 0;">Medico</h1>
                <h1 style="font-size: 20px; text-transform: uppercase; margin: 0;">Life Partner</h1>
                <p style="font-size: 10px; margin: 0;">Bringing Doctors Together</p>
            </td>
        </tr>
    </table>
</div>
        <div id="banner">
            <img src="https://dev-medico.s3.ap-south-1.amazonaws.com/heart345.jpeg" alt="image">
        </div>
        <div id="rohan">
            <h1>Hi {name} 👋</h1>
            <h1>Exciting news! 🎉</h1><br>
            <p style = "font-weight:200">Your interest in {candidate_name} has been accepted on our medico life partner app
              now is your chance to start a conversation and explore the potential for a meaningful connection within
                the medical community</p>

           
            <div>
                <div>
                    <div>
                        <img src="{candidate_img}" alt="boy image" height=100px width="100px">
                    </div>
                    <div>
                        <div>{candidate_mlp}</div>
                        <div>{candidate_name} , {candidate_age} <img src="https://dev-medico.s3.ap-south-1.amazonaws.com/tickemoji.png" height="20px" width="20px" alt="tick emoji"></div>

                    </div>
                </div>
                <h1 class="about">About me</h1>
                <p class="jaipur">{candidate_height},{candidate_grad},{candidate_postgrad},{candidate_caste},{candidate_city}</p>
                <p class="about">Birthdate</p>
                <p class="jaipur">{candidate_dob}</p>

                <div id="pagalu">
                    <div>
                        <p id="chudale">💝 {matched_percentage} Matched</p>
                        <p id="mota">You both matched perfectly</p>
                    </div>
                    <div>
                        <!-- <img src="images/image56.png" alt="image"> -->
                        <div class="ellipse-parent">
                          <div class="ellipse-div"></div>
                          <div class="ellipse-group">
                            <div class="frame-child1"></div>
                            <div class="double-image-wrapper">
                              <div class="double-image">
                               
                              </div>
                            </div>
                          </div>
                        </div>
                    </div>
                </div>

            </div>

        </div>
        <div id="tati">
            <div>
                <p style = "font-weight:200">Get chating and best of luck  your journey to finding love</p>
            </div>
            <div style="padding-left:26%">
                <button>start chating</button>
            </div>
        </div>
        <div id="moto2">
            <div style="text-align: center;">
                <h3>Download the app now</h3>
            </div>
            <table border="0" cellpadding="0" cellspacing="0" style="padding:50px;padding-top:0px;">
              <tr>
                  <td style="width: 60%; vertical-align: top; padding: 0;">
                      <img class="ruhi" src="https://dev-medico.s3.ap-south-1.amazonaws.com/imagehtml.jpeg" alt="">
                  </td>
                  <td style="width: 60%; vertical-align: top; padding: 0;">
                      <img class="ruhi" src="https://dev-medico.s3.ap-south-1.amazonaws.com/image2html.jpeg" alt="">
                  </td>
              </tr>
          </table>
            <div >
              <div >
                <p id="dolor">
                    Our offical customer support numbers and email id are<a href="#"> admin@medicolifepartner.com</a>
                    <span>+918591930074,+919137531284,+919324710288,+918591912971,+919372822836</span> and <span>+919137401531</span></p>
            </div>
            <div>
                <h1 id="lorem">Terms:</h1>
                <p class="elit">1 We at <a href="#">medicolifepartner.com </a> do not verify profile details. Verification of profile of other candidates and any interest to proceed for conversation or marriage with any candidate registered on <a href="#">medicolifepartner.com </a> will be solely candidate's & family's responsibility. Medicolifepartner.com will not take any liability for authenticity of the details mentioned in any individual's profiles nor we will be able to provide documentation support in any legal proceedings.</p><br/>
                <p class="elit">2 Please ensure you only make payments on medicolifepartner App or website. There are many fraud groups and websites who may give false information and commitments - for which members should avoid and will be solely responsible</p><br/>
                <p class="elit">3 Members to take their precaution in sharing information that they are comfortable in sharing on a public domain as your phone, photo, date of birth etc are visible to other members.</p><br/>
                <p class="elit">4 If you are not in agreement with the above, please delete your profile. At any moment if you wish to remove your profile from Medico Life Partner, you can delete your profile after login through the Delete My Account button. Members are requested to remove their profile after their marriage has been finalized.
                    </p><br/>

            </div> 
            <hr />
            <div id="you">
                <p>
    If you no longer want to receive some email please click on <a href="">unsubscribe</a> to adjust your notification
                    settings.</p>
                <p>For any type of support you an email us at <span>admin@medicolifepartner.com</span> or reach us at <span>+918591912971</span>
                </p>
            </div>

           <div id="type" style="margin-left:28%;">
            <a href = "https://www.facebook.com/medicolifepartner/" target="_blank">
                <img src="https://dev-medico.s3.ap-south-1.amazonaws.com/facebook1234.jpeg" width="40px" height="40px" alt="facebook">
            </a>
            <a href="https://www.instagram.com/medicolifepartner/" target="_blank">
                <img src="https://dev-medico.s3.ap-south-1.amazonaws.com/insta1234.jpeg" width="40px" height="40px" alt="insta">
            </a>
            <a href="https://www.linkedin.com/in/medicolifepartner/" target="_blank">
                <img src="https://dev-medico.s3.ap-south-1.amazonaws.com/linkdin1234.jpeg" width="40px" height="40px" alt="linkedin">
            </a>
        </div>



</body>

</html>
'''