Key Naming Conventions
======================
Key Naming Conventionsf or the Redis Library Platform's BIBFRAME keys. These
naming conventions ideally provide semantic meaning in the construction of
the key and related keys. 


## Creative Work Redis instance 
The table below displays the naming pattern used on a typical Creative Work
Redis instance that is usually running on port 6380.

<table>
 <thead>
  <tr>
   <th>Key Schema</th>
   <th>Description</th>
  </tr>
 </thead>
 <tbody>
  <tr>
   <td>bibframe:CreativeWork:{#}</td>
   <td>Redis Hash that is the BIBFRAME root Creative Work. Hash key-values 
       are for atomtic attributes or roles and can be either other Redis Keys
       or be string data such as created_on timestamp.</td>
  </tr>
  <tr>
   <td>bibframe:CreativeWork:{#}:Annotations:facets</td>
   <td>Redis set of Redis keys for BIBFRAME Annotations that function as 
       facets.</td>
  </tr>
  <tr>
   <td>bibframe:CreativeWork:{#}:bibframe:Instances</td>
   <td>Redis set contains the Redis keys of all BIBFRAME Instances that
       are related to the CreativeWork.
  </tr>
  <tr>
   <td>bibframe:CreativeWork:{#}:rda:creator</td>
   <td>Redis set contains Redis keys of BIBFRAME Authorities that
       had a role the creation of the Creative Work.</td>
  </tr>
  <tr>
   <td>bibframe:CreativeWork:{#}:keys</td>
   <td>Redis set contains all of the Redis keys associated with the Creative
       Work, useful for application logic</td>
  </tr>
  <tr>
   <td>bibframe:CreativeWork:{#}:rda:Title</td>
   <td>Redis Hash value for the Creative Work's Title using the RDA
       construction and vocabulary. Common subkeys for this Hash include
       <strong>rda:preferredTitleForWork</strong> and 
       <strong>normed</strong>, and <strong>sort</strong>.</td>
  </tr>
 </tbody>
</table>
       
