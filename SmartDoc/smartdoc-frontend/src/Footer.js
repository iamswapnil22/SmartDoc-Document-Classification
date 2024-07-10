// src/Footer.js
import React from 'react';
import { Box, Container, Grid, Link, Typography } from '@mui/material';

const Footer = () => {
  return (
    <Box
      sx={{
        bgcolor: '#000000', 
        color: 'white', 
        p: 6,
        mt: 'auto',
        boxShadow: '0 -2px 5px rgba(0,0,0,0.1)'
      }}
      component="footer"
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid item xs={12} sm={6}>
            <Typography variant="h6" color="inherit" gutterBottom>
              Footer Content
            </Typography>
            <Typography variant="subtitle1" color="inherit">
              Here you can use rows and columns to organize your footer content. Lorem ipsum dolor sit amet, consectetur adipisicing elit.
            </Typography>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Typography variant="h6" color="inherit" gutterBottom>
              Links
            </Typography>
            <ul style={{ listStyleType: 'none', padding: 0 }}>
              <li>
                <Link href="#" variant="subtitle1" color="inherit">
                  Link 1
                </Link>
              </li>
              <li>
                <Link href="#" variant="subtitle1" color="inherit">
                  Link 2
                </Link>
              </li>
              <li>
                <Link href="#" variant="subtitle1" color="inherit">
                  Link 3
                </Link>
              </li>
              <li>
                <Link href="#" variant="subtitle1" color="inherit">
                  Link 4
                </Link>
              </li>
            </ul>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Typography variant="h6" color="inherit" gutterBottom>
              Links
            </Typography>
            <ul style={{ listStyleType: 'none', padding: 0 }}>
              <li>
                <Link href="www.github.com/iamswapnil22" variant="subtitle1" color="inherit">
                  Github
                </Link>
              </li>
              <li>
                <Link href="https://www.linkedin.com/in/swapnil-shivpuje-182305246/" variant="subtitle1" color="inherit">
                  LinkedIn
                </Link>
              </li>
              <li>
                <Link href="https://x.com/Shivpuje2204" variant="subtitle1" color="inherit">
                  Twitter
                </Link>
              </li>
            </ul>
          </Grid>
        </Grid>
        <Box mt={5}>
          <Typography variant="body2" color="inherit" align="center">
            {'© '}
            {new Date().getFullYear()}
            {' '}
            Swapnil Shivpuje
            {/* <Link color="inherit" href="https://mui.com/">
                Swapnil 
            </Link> */}
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
