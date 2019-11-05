module.exports = async function (req, res, proceed) {

  if (req.session.auth_token && req.session.user_type === 'user') {
    return proceed();
  }

  //--•
  // Otherwise, this request did not come from a logged-in user.
  return res.redirect('/login');

};
